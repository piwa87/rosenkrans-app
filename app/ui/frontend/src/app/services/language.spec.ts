import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { LanguageService } from './language';

describe('LanguageService', () => {
  let service: LanguageService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(LanguageService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should default to English', () => {
    expect(service.language()).toBe('en');
  });

  it('should translate a known key', () => {
    expect(service.t('our_father')).toBe('Our Father');
  });

  it('should translate with placeholders', () => {
    expect(service.t('status_our_father', { decade: 2 })).toContain('2');
  });

  it('should switch language when initLanguage is called', () => {
    service.initLanguage('da');
    expect(service.language()).toBe('da');
    expect(service.t('our_father')).toBe('Fadervor');
  });
});
