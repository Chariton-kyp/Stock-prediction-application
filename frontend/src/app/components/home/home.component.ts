import { AvatarModule } from 'primeng/avatar';
import { ButtonModule } from 'primeng/button';
import { InputSwitchModule } from 'primeng/inputswitch';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { RippleModule } from 'primeng/ripple';
import { StyleClassModule } from 'primeng/styleclass';

import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';

import { AuthService } from '../../services/auth-service.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    InputTextModule,
    InputTextareaModule,
    AvatarModule,
    InputSwitchModule,
    StyleClassModule,
    ButtonModule,
    RippleModule,
    RouterModule,
    HttpClientModule,
  ],
  providers: [AuthService],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent implements OnInit {
  user: any;

  constructor(private authService: AuthService) {}

  ngOnInit(): void {}

  isUserLoggedIn(): boolean {
    return this.authService.isLoggedIn();
  }

  logout(): void {
    this.authService.logout();
  }
}
