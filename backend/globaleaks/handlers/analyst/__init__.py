# -*- coding: utf-8 -*-
#
# Handlers dealing with analyst user functionalities
from sqlalchemy.sql.expression import func, and_

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact

@transact
def get_stats(session, tid, user_id, user_cc, operation, args):
    """
    Transaction for retrieving analyst statistics

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A recipient ID
    :param user_cc: A recipient crypto key
    :param operation: An operation command (grant/revoke)
    :param args: The operation arguments
    """

    num_tips = session.query(func.count(models.InternalTip.id)).one()[0]
    num_tips_no_access = session.query(func.count(models.InternalTip.id)) \
                                .filter(models.InternalTip.access_count == 0).one()[0]
    num_tips_at_least_one_access = num_tips - num_tips_no_access

    num_subscribed_tips = session.query(func.count(models.InternalTip.id)) \
                                .join(models.InternalTipData,
                                      and_(models.InternalTipData.internaltip_id == models.InternalTip.id,
                                           models.InternalTipData.key == 'whistleblower_identity',
                                           models.InternalTipData.creation_date == models.InternalTip.creation_date)).one()[0]
    num_subscribed_later_tips = session.query(func.count(models.InternalTip.id)) \
                                .join(models.InternalTipData,
                                      and_(models.InternalTipData.internaltip_id == models.InternalTip.id,
                                           models.InternalTipData.key == 'whistleblower_identity',
                                           models.InternalTipData.creation_date != models.InternalTip.creation_date)).one()[0]
    num_anonymous_tips = num_tips - num_subscribed_tips - num_subscribed_later_tips

    return {
            # access percentages
            "percentage_no_access": num_tips_no_access/num_tips,
            "percentage_at_least_one_access": num_tips_at_least_one_access/num_tips,
            # subscriptions percentages
            "percentage_anonymous_tips": num_anonymous_tips/num_tips,
            "percentage_subscribed_tips": num_subscribed_tips/num_tips,
            "percentage_subscribed_later_tips": num_subscribed_later_tips/num_tips,
    }

class GetStats(BaseHandler):
    """
    Handler for statistics fetch
    """
    check_roles = 'analyst'

    def get(self):
        return get_stats(self.request.tid,
                         self.session.user_id,
                         self.session.cc,
                         self.request.language,
                         self.request.args)
