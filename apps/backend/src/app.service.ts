import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  getHealth(): object {
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      service: 'SatongPalTang API',
    };
  }

  getVersion(): object {
    return {
      version: '1.0.0',
      name: 'SatongPalTang Multi-tenant Real Estate SaaS',
    };
  }
}
