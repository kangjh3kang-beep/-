'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ArrowLeft, Save } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  code: string;
}

interface User {
  id: string;
  name: string;
  email: string;
}

export default function NewContractPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [salespeople, setSalespeople] = useState<User[]>([]);

  const [formData, setFormData] = useState({
    projectId: '',
    customerName: '',
    customerPhone: '',
    customerEmail: '',
    customerAddress: '',
    unitNumber: '',
    unitType: '',
    unitArea: '',
    contractAmount: '',
    downPayment: '',
    middlePayment: '',
    finalPayment: '',
    salespersonId: '',
    commissionRate: '',
    contractDate: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchProjects();
    fetchSalespeople();
  }, []);

  const fetchProjects = async () => {
    try {
      const { data } = await api.get('/projects');
      setProjects(data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    }
  };

  const fetchSalespeople = async () => {
    try {
      const { data } = await api.get('/users');
      // Filter users with salesperson role (level 60)
      setSalespeople(data);
    } catch (error) {
      console.error('Failed to fetch salespeople:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...formData,
        unitArea: formData.unitArea ? parseFloat(formData.unitArea) : null,
        contractAmount: parseFloat(formData.contractAmount),
        downPayment: formData.downPayment ? parseFloat(formData.downPayment) : null,
        middlePayment: formData.middlePayment ? parseFloat(formData.middlePayment) : null,
        finalPayment: formData.finalPayment ? parseFloat(formData.finalPayment) : null,
        commissionRate: formData.commissionRate ? parseFloat(formData.commissionRate) : null,
        contractDate: formData.contractDate ? new Date(formData.contractDate) : null,
        status: 'DRAFT',
      };

      // Calculate commission amount if rate is provided
      if (payload.commissionRate) {
        payload.commissionAmount = (payload.contractAmount * payload.commissionRate) / 100;
      }

      const { data } = await api.post('/contracts', payload);
      alert('계약이 생성되었습니다.');
      router.push(`/dashboard/contracts/${data.id}`);
    } catch (error: any) {
      console.error('Failed to create contract:', error);
      alert(error.response?.data?.message || '계약 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Auto-calculate final payment
    if (['contractAmount', 'downPayment', 'middlePayment'].includes(name)) {
      const contractAmount = name === 'contractAmount' ? parseFloat(value) || 0 : parseFloat(formData.contractAmount) || 0;
      const downPayment = name === 'downPayment' ? parseFloat(value) || 0 : parseFloat(formData.downPayment) || 0;
      const middlePayment = name === 'middlePayment' ? parseFloat(value) || 0 : parseFloat(formData.middlePayment) || 0;
      const finalPayment = contractAmount - downPayment - middlePayment;
      setFormData((prev) => ({ ...prev, finalPayment: finalPayment.toString() }));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link
          href="/dashboard/contracts"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          계약 목록으로
        </Link>

        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">새 계약 등록</h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Project Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                현장 선택 <span className="text-red-500">*</span>
              </label>
              <select
                name="projectId"
                value={formData.projectId}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                required
              >
                <option value="">현장을 선택하세요</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name} ({project.code})
                  </option>
                ))}
              </select>
            </div>

            {/* Customer Info */}
            <div className="border-t pt-6">
              <h2 className="text-lg font-semibold mb-4">고객 정보</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    고객명 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="customerName"
                    value={formData.customerName}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    연락처 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    name="customerPhone"
                    value={formData.customerPhone}
                    onChange={handleChange}
                    placeholder="010-0000-0000"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">이메일</label>
                  <input
                    type="email"
                    name="customerEmail"
                    value={formData.customerEmail}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">주소</label>
                  <input
                    type="text"
                    name="customerAddress"
                    value={formData.customerAddress}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
            </div>

            {/* Unit Info */}
            <div className="border-t pt-6">
              <h2 className="text-lg font-semibold mb-4">분양 정보</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">호수</label>
                  <input
                    type="text"
                    name="unitNumber"
                    value={formData.unitNumber}
                    onChange={handleChange}
                    placeholder="예: 101동 1001호"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">타입</label>
                  <input
                    type="text"
                    name="unitType"
                    value={formData.unitType}
                    onChange={handleChange}
                    placeholder="예: 84㎡"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">면적(㎡)</label>
                  <input
                    type="number"
                    step="0.01"
                    name="unitArea"
                    value={formData.unitArea}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
            </div>

            {/* Financial Info */}
            <div className="border-t pt-6">
              <h2 className="text-lg font-semibold mb-4">금액 정보</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    총 계약금액 (원) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="contractAmount"
                    value={formData.contractAmount}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    계약금 (원)
                  </label>
                  <input
                    type="number"
                    name="downPayment"
                    value={formData.downPayment}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    중도금 (원)
                  </label>
                  <input
                    type="number"
                    name="middlePayment"
                    value={formData.middlePayment}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">잔금 (원)</label>
                  <input
                    type="number"
                    name="finalPayment"
                    value={formData.finalPayment}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 focus:ring-primary-500 focus:border-primary-500"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">계약일</label>
                  <input
                    type="date"
                    name="contractDate"
                    value={formData.contractDate}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
            </div>

            {/* Salesperson & Commission */}
            <div className="border-t pt-6">
              <h2 className="text-lg font-semibold mb-4">담당자 및 수수료</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">담당 상담사</label>
                  <select
                    name="salespersonId"
                    value={formData.salespersonId}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">선택 안함</option>
                    {salespeople.map((person) => (
                      <option key={person.id} value={person.id}>
                        {person.name} ({person.email})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    수수료율 (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    name="commissionRate"
                    value={formData.commissionRate}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-3 pt-6 border-t">
              <Link
                href="/dashboard/contracts"
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                취소
              </Link>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
              >
                <Save className="w-5 h-5 mr-2" />
                {loading ? '저장 중...' : '계약 등록'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
