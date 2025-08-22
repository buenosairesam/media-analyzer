import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ExecutionManagerComponent } from './execution-manager.component';

describe('ExecutionManagerComponent', () => {
  let component: ExecutionManagerComponent;
  let fixture: ComponentFixture<ExecutionManagerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExecutionManagerComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ExecutionManagerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});