'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Building2, FileText, TrendingUp, Users, LogOut } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  if (!user) {
    return <div className="min-h-screen flex items-center justify-center">로딩 중...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-primary-600">사통팔땅</h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">{user.name}</span>
              <button
                onClick={handleLogout}
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-5 h-5 mr-1" />
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-8">대시보드</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard title="총 현장" value="12" icon={<Building2 className="w-6 h-6" />} />
          <StatCard title="진행 중 계약" value="45" icon={<FileText className="w-6 h-6" />} />
          <StatCard title="이번 달 수익" value="₩234M" icon={<TrendingUp className="w-6 h-6" />} />
          <StatCard title="투자자" value="128" icon={<Users className="w-6 h-6" />} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ModuleCard
            title="현장 관리"
            description="모든 개발 현장을 통합 관리하세요"
            href="/dashboard/projects"
            icon={<Building2 className="w-8 h-8" />}
          />
          <ModuleCard
            title="계약 관리"
            description="전자계약 및 분양 관리"
            href="/dashboard/contracts"
            icon={<FileText className="w-8 h-8" />}
          />
          <ModuleCard
            title="수지 관리"
            description="실시간 회계 및 예산 관리"
            href="/dashboard/finance"
            icon={<TrendingUp className="w-8 h-8" />}
          />
          <ModuleCard
            title="투자자 관리"
            description="리츠 및 NFT 투자 관리"
            href="/dashboard/investors"
            icon={<Users className="w-8 h-8" />}
          />
        </div>
      </main>
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-600 text-sm">{title}</span>
        <div className="text-primary-600">{icon}</div>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function ModuleCard({
  title,
  description,
  href,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow"
    >
      <div className="text-primary-600 mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </Link>
  );
}
