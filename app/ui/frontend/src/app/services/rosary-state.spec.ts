import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { RosaryStateService } from './rosary-state';

describe('RosaryStateService', () => {
  let service: RosaryStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(RosaryStateService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should start with null state', () => {
    expect(service.state()).toBeNull();
  });
});
