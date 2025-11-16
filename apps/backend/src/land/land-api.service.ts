import { Injectable, HttpException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';

@Injectable()
export class LandApiService {
  private readonly apiBaseUrl = 'https://www.eum.go.kr/web/am/api';
  private readonly apiKey: string;

  constructor(private configService: ConfigService) {
    this.apiKey = this.configService.get<string>('LAND_API_KEY') || '';
  }

  /**
   * 토지이음 API - 토지이용계획 조회
   * @param pnu 필지고유번호 (19자리)
   */
  async getLandUsePlan(pnu: string) {
    if (!this.apiKey) {
      throw new HttpException('토지이음 API 키가 설정되지 않았습니다', 500);
    }

    try {
      const response = await axios.get(`${this.apiBaseUrl}/landUsePlan`, {
        params: {
          pnu,
          serviceKey: this.apiKey,
        },
        timeout: 10000,
      });

      return this.parseLandUsePlanResponse(response.data);
    } catch (error) {
      console.error('토지이음 API 오류:', error);
      throw new HttpException('토지이용계획 조회 실패', 500);
    }
  }

  /**
   * 주소로 PNU (필지고유번호) 조회
   */
  async getPnuByAddress(address: string) {
    // 실제 구현에는 주소 -> PNU 변환 API 호출
    // 여기서는 예시 구조만 제공
    return {
      pnu: '1111012300106680001',
      address,
    };
  }

  /**
   * 토지이용계획 응답 파싱
   */
  private parseLandUsePlanResponse(data: any) {
    // API 응답을 파싱하여 필요한 정보 추출
    const items = data?.response?.body?.items?.item || [];

    return {
      // 용도지역
      zoning: this.extractValue(items, '용도지역'),

      // 용도지구
      landUseDistrict: this.extractValue(items, '용도지구'),

      // 지구단위계획구역
      districtPlan: this.extractValue(items, '지구단위계획구역'),

      // 건폐율
      buildingCoverageRatio: this.extractNumericValue(items, '건폐율'),

      // 용적률
      floorAreaRatio: this.extractNumericValue(items, '용적률'),

      // 높이제한
      heightLimit: this.extractValue(items, '높이제한'),

      // 기타 제한사항
      restrictions: items.filter((item: any) =>
        !['용도지역', '용도지구', '지구단위계획구역', '건폐율', '용적률', '높이제한'].includes(item.cnflcAtNm)
      ),

      // 전체 응답 데이터
      rawData: data,
    };
  }

  /**
   * API 응답에서 특정 값 추출
   */
  private extractValue(items: any[], fieldName: string): string | null {
    const item = items.find((i: any) => i.cnflcAtNm === fieldName);
    return item?.cnflcAtNm || null;
  }

  /**
   * API 응답에서 숫자 값 추출
   */
  private extractNumericValue(items: any[], fieldName: string): number | null {
    const value = this.extractValue(items, fieldName);
    if (!value) return null;

    // "60% 이하" 같은 형식에서 숫자만 추출
    const match = value.match(/(\d+\.?\d*)/);
    return match ? parseFloat(match[1]) : null;
  }

  /**
   * 건축 가능 항목 분석
   */
  async analyzeBuildingPossibilities(pnu: string) {
    const landPlan = await this.getLandUsePlan(pnu);

    const possibilities = [];

    // 용도지역에 따른 건축 가능 항목 판단
    const zoning = landPlan.zoning;
    if (zoning) {
      if (zoning.includes('주거지역')) {
        possibilities.push('단독주택', '공동주택', '근린생활시설');
      }
      if (zoning.includes('상업지역')) {
        possibilities.push('판매시설', '업무시설', '숙박시설');
      }
      if (zoning.includes('공업지역')) {
        possibilities.push('공장', '창고시설', '위험물저장시설');
      }
    }

    return {
      ...landPlan,
      buildingPossible: possibilities,
    };
  }
}
