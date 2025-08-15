import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalysisPanelComponent } from './analysis-panel.component';

describe('AnalysisPanelComponent', () => {
  let component: AnalysisPanelComponent;
  let fixture: ComponentFixture<AnalysisPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnalysisPanelComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(AnalysisPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
