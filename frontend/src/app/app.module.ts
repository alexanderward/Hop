import { BrowserModule, Title } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

// *******************************************************************************
// NgBootstrap

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

// *******************************************************************************
// App

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { AppService } from './app.service';
import { LayoutModule } from './layout/layout.module';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
// *******************************************************************************
// Pages

import { HomeComponent } from './home/home.component';
import { StackComponent } from './stack/stack.component';
import { StackService } from './services/stack.service';
import { HttpClientModule } from '@angular/common/http';
import { ToastrService, ToastrModule } from 'ngx-toastr';

// *******************************************************************************
//

@NgModule({
  declarations: [
    AppComponent,

    // Pages
    HomeComponent,
    StackComponent
  ],

  imports: [
    BrowserModule,
    NgbModule.forRoot(),
    NgxDatatableModule,
    // App
    AppRoutingModule,
    LayoutModule,
    HttpClientModule,
    BrowserAnimationsModule,
    ToastrModule.forRoot()
  ],

  providers: [
    Title,
    AppService,
    StackService
  ],

  bootstrap: [
    AppComponent
  ]
})
export class AppModule { }
