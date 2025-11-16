import { Module } from '@nestjs/common';
import { TerminationController } from './termination.controller';
import { TerminationService } from './termination.service';

@Module({
  controllers: [TerminationController],
  providers: [TerminationService],
})
export class TerminationModule {}
