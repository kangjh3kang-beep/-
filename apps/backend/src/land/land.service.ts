import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { LandApiService } from './land-api.service';

@Injectable()
export class LandService {
  constructor(
    private prisma: PrismaService,
    private landApiService: LandApiService,
  ) {}

  async create(tenantId: string, data: any) {
    return this.prisma.land.create({
      data: {
        ...data,
        tenantId,
      },
      include: {
        project: { select: { id: true, name: true } },
      },
    });
  }

  async findAll(tenantId: string, projectId?: string) {
    return this.prisma.land.findMany({
      where: {
        tenantId,
        ...(projectId && { projectId }),
      },
      include: {
        project: { select: { id: true, name: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async findOne(id: string, tenantId: string) {
    return this.prisma.land.findFirst({
      where: { id, tenantId },
      include: {
        project: true,
      },
    });
  }

  async update(id: string, data: any) {
    return this.prisma.land.update({
      where: { id },
      data,
    });
  }

  async delete(id: string) {
    return this.prisma.land.delete({
      where: { id },
    });
  }

  /**
   * 토지이음 API로 토지 정보 조회 및 업데이트
   */
  async fetchLandInfo(id: string, tenantId: string) {
    const land = await this.findOne(id, tenantId);
    if (!land || !land.pnu) {
      throw new Error('PNU가 없습니다. 먼저 필지고유번호를 입력해주세요.');
    }

    // 토지이음 API 호출
    const landInfo = await this.landApiService.analyzeBuildingPossibilities(land.pnu);

    // DB 업데이트
    return this.prisma.land.update({
      where: { id },
      data: {
        zoning: landInfo.zoning,
        landUseDistrict: landInfo.landUseDistrict,
        districtPlan: landInfo.districtPlan,
        buildingCoverageRatio: landInfo.buildingCoverageRatio,
        floorAreaRatio: landInfo.floorAreaRatio,
        heightLimit: landInfo.heightLimit,
        buildingPossible: landInfo.buildingPossible,
        apiData: landInfo.rawData,
        apiLastFetched: new Date(),
      },
    });
  }

  /**
   * 엑셀에서 토지 목록 일괄 등록
   */
  async bulkCreate(tenantId: string, projectId: string, lands: any[]) {
    const results = [];

    for (const landData of lands) {
      try {
        const created = await this.prisma.land.create({
          data: {
            tenantId,
            projectId,
            ...landData,
          },
        });

        // PNU가 있으면 자동으로 토지 정보 조회
        if (landData.pnu) {
          try {
            await this.fetchLandInfo(created.id, tenantId);
            results.push({ success: true, land: created });
          } catch (error) {
            results.push({ success: false, land: created, error: '토지정보 조회 실패' });
          }
        } else {
          results.push({ success: true, land: created });
        }
      } catch (error) {
        results.push({ success: false, error: error.message, data: landData });
      }
    }

    return results;
  }
}
