import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-execution-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="source-management disabled">
      <div class="section-header" (click)="toggleSection()">
        <h4>Execution Manager</h4>
        <span class="toggle-icon">{{ showContent ? '−' : '+' }}</span>
      </div>
      
      <div class="management-content" *ngIf="showContent">
        <div class="execution-modes">
          <div class="mode-option" *ngFor="let mode of executionModes">
            <label class="radio-container">
              <input 
                type="radio" 
                name="executionMode" 
                [value]="mode.id"
                [(ngModel)]="selectedExecution"
                disabled>
              <span>{{ mode.label }}</span>
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

    .execution-modes {
      margin-bottom: 15px;
    }

    .mode-option {
      margin-bottom: 8px;
    }

    .radio-container {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
    }

    .radio-container input[type="radio"] {
      opacity: 0.4;
    }

    .radio-container span {
      opacity: 0.6;
      color: #6c757d;
    }
  `]
})
export class ExecutionManagerComponent {
  selectedExecution: string = 'local';
  showContent = false;
  
  executionModes = [
    { id: 'local', label: 'Local' },
    { id: 'lan', label: 'LAN' },
    { id: 'cloud', label: 'Cloud' }
  ];

  toggleSection() {
    this.showContent = !this.showContent;
  }
}