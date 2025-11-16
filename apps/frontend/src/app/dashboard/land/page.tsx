'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Upload, Download, RefreshCw, MapPin, FileText, Plus, Search } from 'lucide-react';
import Link from 'next/link';

interface Project {
  id: string;
  name: string;
  code: string;
}

interface Land {
  id: string;
  projectId: string;
  project?: Project;
  address: string;
  lotNumber: string;
  pnu?: string;
  landArea?: number;
  zoning?: string;
  landUseDistrict?: string;
  buildingCoverageRatio?: number;
  floorAreaRatio?: number;
  heightLimit?: string;
  buildingPossible?: string[];
  apiLastFetched?: string;
  notes?: string;
  createdAt: string;
}

export default function LandManagementPage() {
  const [lands, setLands] = useState<Land[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchLands();
    }
  }, [selectedProject]);

  const fetchProjects = async () => {
    try {
      const { data } = await api.get('/projects');
      setProjects(data);
      if (data.length > 0) {
        setSelectedProject(data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    }
  };

  const fetchLands = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/land', {
        params: { projectId: selectedProject },
      });
      setLands(data);
    } catch (error) {
      console.error('Failed to fetch lands:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      // Parse Excel file (you would need a library like xlsx for this)
      // For now, this is a placeholder implementation
      const formData = new FormData();
      formData.append('file', file);

      // This would parse the Excel and send to the bulk endpoint
      alert('Excel 파일 파싱 기능은 구현 중입니다. 직접 데이터를 입력해주세요.');

      // Example structure of bulk create:
      // const lands = parsedExcelData.map(row => ({
      //   address: row.address,
      //   lotNumber: row.lotNumber,
      //   pnu: row.pnu,
      //   landArea: row.landArea,
      // }));
      // await api.post('/land/bulk', {
      //   projectId: selectedProject,
      //   lands,
      //   fetchApiData: true,
      // });
      // fetchLands();
    } catch (error) {
      console.error('Failed to upload file:', error);
      alert('파일 업로드에 실패했습니다.');
    } finally {
      setUploading(false);
    }
  };

  const fetchLandInfo = async (landId: string) => {
    try {
      await api.post(`/land/${landId}/fetch-info`);
      alert('토지 정보를 성공적으로 가져왔습니다.');
      fetchLands();
    } catch (error: any) {
      console.error('Failed to fetch land info:', error);
      alert(error.response?.data?.message || '토지 정보 조회에 실패했습니다.');
    }
  };

  const downloadTemplate = () => {
    // Create CSV template
    const template = 'address,lotNumber,pnu,landArea\n예) 서울특별시 강남구 역삼동,123-45,1168010100101230045,1000.00';
    const blob = new Blob([template], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'land_template.csv';
    a.click();
  };

  const filteredLands = lands.filter(
    (land) =>
      land.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      land.lotNumber?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      land.pnu?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">토지 조서 관리</h1>
          <p className="text-gray-600 mt-1">토지 지번 목록을 관리하고 토지이음 API로 상세 정보를 조회하세요</p>
        </div>

        {/* Project Selection and Actions */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">현장 선택</label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name} ({project.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={downloadTemplate}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                <Download className="w-5 h-5 mr-2" />
                템플릿 다운로드
              </button>

              <label className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 cursor-pointer">
                <Upload className="w-5 h-5 mr-2" />
                {uploading ? '업로드 중...' : 'Excel 업로드'}
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={uploading || !selectedProject}
                />
              </label>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="주소, 지번, PNU로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        {/* Land List */}
        {loading ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-gray-500">로딩 중...</div>
          </div>
        ) : filteredLands.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">등록된 토지가 없습니다.</p>
            <p className="text-sm text-gray-400 mt-2">Excel 파일을 업로드하여 토지 목록을 등록하세요.</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      주소
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      지번
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      PNU
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      면적(㎡)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      용도지역
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      건폐율
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      용적률
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      건축가능항목
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      작업
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredLands.map((land) => (
                    <tr key={land.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">{land.address}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{land.lotNumber}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{land.pnu || '-'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {land.landArea ? land.landArea.toLocaleString() : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{land.zoning || '-'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {land.buildingCoverageRatio ? `${land.buildingCoverageRatio}%` : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {land.floorAreaRatio ? `${land.floorAreaRatio}%` : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          {land.buildingPossible && land.buildingPossible.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {land.buildingPossible.map((item, idx) => (
                                <span
                                  key={idx}
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800"
                                >
                                  {item}
                                </span>
                              ))}
                            </div>
                          ) : (
                            '-'
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => fetchLandInfo(land.id)}
                          className="text-primary-600 hover:text-primary-900 inline-flex items-center"
                          disabled={!land.pnu}
                          title={!land.pnu ? 'PNU가 필요합니다' : '토지이음 API로 정보 조회'}
                        >
                          <RefreshCw className="w-4 h-4 mr-1" />
                          {land.apiLastFetched ? '재조회' : '정보조회'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <FileText className="w-5 h-5 text-blue-600 mr-3 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-semibold mb-2">토지이음 API 연동 안내</p>
              <ul className="list-disc list-inside space-y-1">
                <li>PNU(필지고유번호)가 입력된 토지만 자동 조회가 가능합니다.</li>
                <li>정보조회 버튼을 클릭하면 용도지역, 건폐율, 용적률, 건축가능항목 등이 자동으로 업데이트됩니다.</li>
                <li>Excel 업로드 시 PNU를 함께 입력하면 일괄 조회가 가능합니다.</li>
                <li>
                  PNU는 19자리 숫자로 구성됩니다. (예: 1168010100101230045)
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
