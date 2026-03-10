import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { LanguageSelector } from './language-selector';

describe('LanguageSelector', () => {
  let component: LanguageSelector;
  let fixture: ComponentFixture<LanguageSelector>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LanguageSelector],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(LanguageSelector);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should list supported languages', () => {
    expect(component.supportedLanguages.length).toBeGreaterThanOrEqual(2);
    const codes = component.supportedLanguages.map(([code]) => code);
    expect(codes).toContain('en');
    expect(codes).toContain('da');
  });

  it('should render a select element', () => {
    fixture.detectChanges();
    const select = fixture.nativeElement.querySelector('select');
    expect(select).toBeTruthy();
  });
});
