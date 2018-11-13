import { Component, OnInit } from '@angular/core';
import { AppService } from '../app.service';
import { StackService } from '../services/stack.service';
import { Subject, BehaviorSubject, interval } from 'rxjs';
import { takeUntil, switchMap, tap, map, catchError } from 'rxjs/operators';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-stack',
  templateUrl: './stack.component.html'
})
export class StackComponent implements OnInit {
  loadingIndicator = false;
  rows = [];
  temp = [];
  selected = [];

  infrastructureTags = {
    services: ['ec2', 'rds']
  }

  $refresh = new BehaviorSubject(true);

  $start = new Subject();
  $stop = new Subject();

  $unSubscribe = new Subject();

  constructor(private appService: AppService, private stackService: StackService, private toastrService: ToastrService) {
    this.appService.pageTitle = 'Stack';
  }

  ngOnInit() {
    this.$refresh.pipe(
      tap(() => {
        this.loadingIndicator = true;
        this.selected = [];
      }),
      takeUntil(this.$unSubscribe),
      switchMap(() => this.stackService.getState())
    ).subscribe((results: any) => {
      this.rows = results.instances;
      this.loadingIndicator = false;
    }, error => { this.loadingIndicator = false; });

    this.$start.pipe(
      tap(() => {
        this.loadingIndicator = true;
      }),
      map((selected: any) => selected.filter((record) => record.status == 'stopped')),
      takeUntil(this.$unSubscribe),
      switchMap(ids => this.stackService.start({ ids: ids }))
    ).subscribe((results: any) => {
      this.toastrService.success('Started Instances', 'Stack Action - Start')
      this.loadingIndicator = false;
      this.$refresh.next(null);
    }, error => {
      this.loadingIndicator = false;
      this.selected = [];
      this.toastrService.error('Failed to start Instances', 'Stack Action - Start')
    });

    this.$stop.pipe(
      tap(() => {
        this.loadingIndicator = true;
      }),
      takeUntil(this.$unSubscribe),
      map((selected: any) => selected.filter((record) => record.status == 'running' || record.status == 'available')),
      switchMap(ids => this.stackService.stop({ ids: ids }))
    ).subscribe((results: any) => {
      this.toastrService.success('Stopped Instances', 'Stack Action - Stop')
      this.loadingIndicator = false;
      this.$refresh.next(null);
    }, error => {
      this.loadingIndicator = false;
      this.selected = [];
      this.toastrService.error('Failed to stop Instances', 'Stack Action - Stop')
    });

  }

  onSelect(event) {
    this.selected = event.selected;
  }

  start() {

  }



}
