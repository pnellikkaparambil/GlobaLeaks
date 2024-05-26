import {Component, Input} from "@angular/core";
import {NgbActiveModal, NgbModal} from "@ng-bootstrap/ng-bootstrap";

@Component({
  selector: "src-confirmation",
  templateUrl: "./confirmation.component.html"
})
export class ConfirmationComponent {
  @Input() arg: string;

  constructor(private modalService: NgbModal, private activeModal: NgbActiveModal) {
  }

  confirmFunction: (secret: string) => void;

  confirm(arg: string) {
    this.confirmFunction(arg);
    return this.activeModal.close(arg);
  }

  cancel() {
    this.modalService.dismissAll();
  }
}
