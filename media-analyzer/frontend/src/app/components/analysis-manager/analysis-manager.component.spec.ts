import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AnalysisManagerComponent } from './analysis-manager.component';

describe('AnalysisManagerComponent', () => {
  let component: AnalysisManagerComponent;
  let fixture: ComponentFixture<AnalysisManagerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnalysisManagerComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(AnalysisManagerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});