import {Inject, Injectable, Renderer2} from "@angular/core";
import {LangChangeEvent, TranslateService} from "@ngx-translate/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {DOCUMENT} from "@angular/common";

@Injectable({
  providedIn: "root",
})
export class TranslationService {

  language = "";
  public currentDirection: string;

  constructor(private utilsService: UtilsService, protected translate: TranslateService, @Inject(DOCUMENT) private document: Document) {
    this.currentDirection = this.utilsService.getDirection(this.translate.currentLang);
  }

  loadBootstrapStyles(event: LangChangeEvent, renderer: Renderer2) {
    let waitForLoader = false;
    const newDirection = this.utilsService.getDirection(event.lang);
    if (newDirection !== this.currentDirection) {
      waitForLoader = true;
      this.utilsService.removeStyles(renderer, this.document, "css/styles-" + this.currentDirection + ".css");

      const lang = this.translate.currentLang;
      const cssFilename = ['ar', 'dv', 'fa', 'fa_AF', 'he', 'ps', 'ug', 'ur'].includes(lang) ? 'styles-rtl.css' : 'styles-ltr.css';
      const cssPath = `css/${cssFilename}`;
      const newLinkElement = renderer.createElement('link');
      renderer.setAttribute(newLinkElement, 'rel', 'stylesheet');
      renderer.setAttribute(newLinkElement, 'type', 'text/css');
      renderer.setAttribute(newLinkElement, 'href', cssPath);
      const firstLink = this.document.head.querySelector('link');
      renderer.insertBefore(this.document.head, newLinkElement, firstLink);
      this.currentDirection = newDirection;
    }
    return waitForLoader;
  }

  onChange(changedLanguage: string, callback?: () => void) {
    this.language = changedLanguage;
    this.translate.use(this.language).subscribe(() => {
      this.translate.setDefaultLang(this.language);
      if (callback) {
        callback();
      }
    });
  }
}
