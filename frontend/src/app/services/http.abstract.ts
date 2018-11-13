import { HttpClient } from '@angular/common/http';
import { isNull } from 'util';
import { environment } from '../../environments/environment';

export abstract class HTTPBase {

    url = environment.url;
    constructor(private http: HttpClient, path) {
        this.url = `${this.url}/${path}`;
    }

    private buildUrl(url: string, queryStrings: {} = null) {
        url = `${this.url}/${url}`;
        if (!isNull(queryStrings)) {
            url = `${url}?`
            let qs = [];
            Object.keys(queryStrings).forEach(key => {
                qs.push(`${key}=${queryStrings[key]}`)
            })
            url = `${url}` + qs.join('&');
        }
        return url;
    }

    protected get(url: string, queryStrings: {} = null) {
        const fqdn = this.buildUrl(url, queryStrings);
        return this.http.get(fqdn);
    }

    protected post(url: string, data) {
        const fqdn = this.buildUrl(url);
        return this.http.post(fqdn, data);
    }

    protected put() { }

    protected delete() { }
}