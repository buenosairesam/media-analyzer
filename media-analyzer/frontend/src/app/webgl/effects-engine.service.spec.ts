import { TestBed } from '@angular/core/testing';

import { EffectsEngineService } from './effects-engine.service';

describe('EffectsEngineService', () => {
  let service: EffectsEngineService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(EffectsEngineService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
