import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-analysis-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="source-management disabled">
      <div class="section-header" (click)="toggleSection()">
        <h4>Analysis Manager</h4>
        <span class="toggle-icon">{{ showContent ? '−' : '+' }}</span>
      </div>
      
      <div class="management-content" *ngIf="showContent">
        <div class="analysis-features">
          <div class="feature-option" *ngFor="let feature of analysisFeatures">
            <label class="checkbox-container">
              <input 
                type="checkbox" 
                [checked]="feature.enabled"
                disabled>
              <span>{{ feature.label }}</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .source-management {
      border: 1px solid #dee2e6;
      border-radius: 6px;
      overflow: hidden;
    }

    .source-management.disabled {
      opacity: 0.6;
    }

    .section-header {
      background: #e9ecef;
      padding: 12px 15px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      user-select: none;
    }

    .disabled .section-header {
      background: #e0e0e0;
    }

    .section-header:hover {
      background: #dee2e6;
    }

    .disabled .section-header:hover {
      background: #e0e0e0;
    }

    .section-header h4 {
      margin: 0;
      color: #495057;
      font-size: 14px;
    }

    .disabled .section-header h4 {
      color: #6c757d;
    }

    .toggle-icon {
      font-weight: bold;
      color: #6c757d;
    }

    .management-content {
      padding: 15px;
      background: white;
    }

    .disabled .management-content {
      background: #f8f8f8;
    }

    .analysis-features {
      margin-bottom: 15px;
    }

    .feature-option {
      margin-bottom: 8px;
    }

    .checkbox-container {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
    }

    .checkbox-container input[type="checkbox"] {
      opacity: 0.4;
    }

    .checkbox-container span {
      opacity: 0.6;
      color: #6c757d;
    }
  `]
})
export class AnalysisManagerComponent {
  showContent = false;
  
  analysisFeatures = [
    { id: 'logo_detection', label: 'Logo Detection', enabled: true, available: true },
    { id: 'visual_properties', label: 'Visual Properties', enabled: false, available: false },
    { id: 'object_detection', label: 'Object Detection', enabled: false, available: false },
    { id: 'audio_transcript', label: 'Audio Transcript', enabled: false, available: false },
    { id: 'text_recognition', label: 'Text Recognition', enabled: false, available: false }
  ];

  toggleSection() {
    this.showContent = !this.showContent;
  }

  get activeFeatures() {
    return this.analysisFeatures.filter(f => f.enabled).length;
  }

  get availableFeatures() {
    return this.analysisFeatures.filter(f => f.available).length;
  }
}