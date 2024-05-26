import {Directive, HostListener} from "@angular/core";

@Directive({
  selector: "[disableCcp]"
})
export class DisableCcpDirective {
  @HostListener("cut", ["$event"])
  @HostListener("copy", ["$event"])
  @HostListener("paste", ["$event"])
  onCutCopyPaste(event: Event) {
    event.preventDefault();
  }
}