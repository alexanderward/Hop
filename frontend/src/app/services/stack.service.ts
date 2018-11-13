import { Injectable, Inject } from '@angular/core';
import { HTTPBase } from './http.abstract';
import { HttpClient } from '@angular/common/http';

@Injectable()
export class StackService extends HTTPBase {

  constructor(@Inject(HttpClient) http: HttpClient) {
    super(http, 'stack');
  }

  public getState() {
    return this.get('get-state');
  }

  public start(data) {
    
    return this.post('start', data);
  }

  public stop(data) {
    return this.post('stop', data);
  }

}
