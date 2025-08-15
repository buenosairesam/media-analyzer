import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StreamControlComponent } from './stream-control.component';

describe('StreamControlComponent', () => {
  let component: StreamControlComponent;
  let fixture: ComponentFixture<StreamControlComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StreamControlComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(StreamControlComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
