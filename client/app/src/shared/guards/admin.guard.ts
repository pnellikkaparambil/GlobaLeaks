import {Injectable} from "@angular/core";
import {ActivatedRoute, Router, UrlTree} from "@angular/router";
import {Observable} from "rxjs";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppConfigService} from "@app/services/root/app-config.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Injectable({
  providedIn: "root"
})
export class AdminGuard {
  constructor(private activatedRoute: ActivatedRoute, private utilsService: UtilsService, private router: Router, private appConfigService: AppConfigService, public authenticationService: AuthenticationService) {
  }

  canActivate(): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    if (this.authenticationService.session) {
      if(this.authenticationService.session.role === "admin"){
        this.appConfigService.setPage(this.router.url);
      }else {
        this.router.navigateByUrl("/login").then();
      }
      return true;
    } else {
      this.utilsService.routeGuardRedirect('login', true);
      return false;
    }
  }
}
