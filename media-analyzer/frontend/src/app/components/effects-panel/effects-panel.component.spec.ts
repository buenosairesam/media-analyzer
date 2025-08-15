import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EffectsPanelComponent } from './effects-panel.component';

describe('EffectsPanelComponent', () => {
  let component: EffectsPanelComponent;
  let fixture: ComponentFixture<EffectsPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EffectsPanelComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(EffectsPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
