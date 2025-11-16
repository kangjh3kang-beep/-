import { Module } from '@nestjs/common';
import { LandController } from './land.controller';
import { LandService } from './land.service';
import { LandApiService } from './land-api.service';

@Module({
  controllers: [LandController],
  providers: [LandService, LandApiService],
  exports: [LandService],
})
export class LandModule {}
