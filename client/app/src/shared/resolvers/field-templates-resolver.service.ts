import {Injectable} from "@angular/core";
import {Observable, of} from "rxjs";
import {map} from "rxjs/operators";
import {HttpService} from "@app/shared/services/http.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {fieldtemplatesResolverModel} from "@app/models/resolvers/field-template-model";

@Injectable({
  providedIn: "root"
})
export class FieldTemplatesResolver {
  dataModel: fieldtemplatesResolverModel[];

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "admin") {
      return this.httpService.requestAdminFieldTemplateResource().pipe(
        map((response: fieldtemplatesResolverModel[]) => {
          this.dataModel = response;
          return true;
        })
      );
    }
    return of(true);
  }
}
