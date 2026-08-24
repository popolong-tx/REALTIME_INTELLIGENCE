import React, { useState, useEffect } from 'react';

interface PlanVersion {
  id: string;
  version: number;
  createdAt: string;
  createdBy: string;
  status: 'draft' | 'active' | 'completed' | 'cancelled';
  parameters: {
    symbol: string;
    targetReturn: number;
    riskLevel: string;
    timeHorizon: string;
    entryPrice: number;
    targetPrice: number;
    stopLoss: number;
  };
  performance?: {
    actualReturn: number;
    maxDrawdown: number;
    winRate: number;
  };
}

interface PlanVersionComparisonProps {
  planId: string;
  className?: string;
}

const PlanVersionComparison: React.FC<PlanVersionComparisonProps> = ({
  planId,
  className = '',
}) => {
  const [versions, setVersions] = useState<PlanVersion[]>([]);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch versions
  useEffect(() => {
    const fetchVersions = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/v1/plans/${planId}/versions`);
        const data = await response.json();
        setVersions(data.versions || []);
      } catch (error) {
        console.error('Error fetching versions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchVersions();
  }, [planId]);

  // Toggle version selection
  const toggleVersion = (versionId: string) => {
    setSelectedVersions((prev) => {
      if (prev.includes(versionId)) {
        return prev.filter((id) => id !== versionId);
      }
      if (prev.length >= 3) {
        return prev; // Max 3 versions
      }
      return [...prev, versionId];
    });
  };

  // Get selected version data
  const selectedVersionData = versions.filter((v) =>
    selectedVersions.includes(v.id)
  );

  // Status badge
  const StatusBadge: React.FC<{ status: PlanVersion['status'] }> = ({ status }) => {
    const config = {
      draft: { label: '草稿', color: 'gray' },
      active: { label: '进行中', color: 'blue' },
      completed: { label: '已完成', color: 'green' },
      cancelled: { label: '已取消', color: 'red' },
    };

    const { label, color } = config[status];

    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800`}
      >
        {label}
      </span>
    );
  };

  // Comparison table
  const ComparisonTable: React.FC = () => {
    if (selectedVersionData.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>请选择最多3个版本进行比较</p>
        </div>
      );
    }

    const rows = [
      {
        label: '创建时间',
        getValue: (v: PlanVersion) => new Date(v.createdAt).toLocaleString(),
      },
      {
        label: '创建者',
        getValue: (v: PlanVersion) => v.createdBy,
      },
      {
        label: '状态',
        getValue: (v: PlanVersion) => <StatusBadge status={v.status} />,
      },
      {
        label: '目标收益率',
        getValue: (v: PlanVersion) => `${v.parameters.targetReturn}%`,
      },
      {
        label: '风险等级',
        getValue: (v: PlanVersion) => v.parameters.riskLevel,
      },
      {
        label: '投资期限',
        getValue: (v: PlanVersion) => v.parameters.timeHorizon,
      },
      {
        label: '入场价',
        getValue: (v: PlanVersion) => `$${v.parameters.entryPrice?.toFixed(2)}`,
      },
      {
        label: '目标价',
        getValue: (v: PlanVersion) => `$${v.parameters.targetPrice?.toFixed(2)}`,
      },
      {
        label: '止损价',
        getValue: (v: PlanVersion) => `$${v.parameters.stopLoss?.toFixed(2)}`,
      },
      {
        label: '实际收益',
        getValue: (v: PlanVersion) =>
          v.performance
            ? `${v.performance.actualReturn.toFixed(2)}%`
            : '-',
      },
      {
        label: '最大回撤',
        getValue: (v: PlanVersion) =>
          v.performance
            ? `${v.performance.maxDrawdown.toFixed(2)}%`
            : '-',
      },
      {
        label: '胜率',
        getValue: (v: PlanVersion) =>
          v.performance
            ? `${(v.performance.winRate * 100).toFixed(1)}%`
            : '-',
      },
    ];

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                属性
              </th>
              {selectedVersionData.map((version) => (
                <th
                  key={version.id}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  版本 {version.version}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rows.map((row) => (
              <tr key={row.label}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {row.label}
                </td>
                {selectedVersionData.map((version) => (
                  <td
                    key={version.id}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                  >
                    {row.getValue(version)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Version selector
  const VersionSelector: React.FC = () => (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-gray-700">选择版本进行比较</h4>
      <div className="space-y-2">
        {versions.map((version) => (
          <label
            key={version.id}
            className={`flex items-center p-3 border rounded-lg cursor-pointer ${
              selectedVersions.includes(version.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <input
              type="checkbox"
              checked={selectedVersions.includes(version.id)}
              onChange={() => toggleVersion(version.id)}
              disabled={
                !selectedVersions.includes(version.id) &&
                selectedVersions.length >= 3
              }
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <div className="ml-3 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">
                  版本 {version.version}
                </span>
                <StatusBadge status={version.status} />
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {new Date(version.createdAt).toLocaleString()} • {version.createdBy}
              </div>
            </div>
          </label>
        ))}
      </div>
    </div>
  );

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">版本比较</h2>
        <p className="text-sm text-gray-500 mt-1">
          比较不同版本的交易计划参数和表现
        </p>
      </div>

      {/* Content */}
      <div className="p-4">
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">加载版本历史...</p>
          </div>
        ) : (
          <div className="space-y-6">
            <VersionSelector />
            <ComparisonTable />
          </div>
        )}
      </div>
    </div>
  );
};

export default PlanVersionComparison;
