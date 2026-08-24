import React, { useState } from 'react';

interface DisclaimerProps {
  type?: 'general' | 'recommendation' | 'model' | 'risk';
  compact?: boolean;
  onAccept?: () => void;
  className?: string;
}

const DISCLAIMERS = {
  general: {
    title: '免责声明',
    content: `本软件提供的所有信息仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。

在做出任何投资决策之前，请您：
• 充分了解相关投资产品的特性和风险
• 根据自身的风险承受能力和投资目标做出决策
• 必要时咨询专业的投资顾问

本软件不对任何投资损失承担责任。`,
    icon: '⚖️',
  },
  recommendation: {
    title: '交易建议声明',
    content: `本系统生成的交易建议仅供参考，不构成买卖指令。

• 建议基于历史数据和算法模型，不代表未来表现
• 市场条件可能发生变化，建议可能失效
• 请结合自身判断和专业意见做出决策
• 所有投资决策由投资者本人负责

过往业绩不代表未来收益。`,
    icon: '📊',
  },
  model: {
    title: '模型说明',
    content: `本系统使用的量化模型具有以下局限性：

• 模型基于历史数据训练，可能无法准确预测未来
• 模型可能受到数据质量和完整性的影响
• 市场极端情况下模型可能失效
• 模型结果需要结合人工判断使用

模型输出不构成投资建议。`,
    icon: '🤖',
  },
  risk: {
    title: '风险警示',
    content: `投资涉及风险，包括但不限于：

• 市场风险：市场价格波动可能导致损失
• 流动性风险：某些资产可能难以快速变现
• 信用风险：交易对手可能违约
• 操作风险：系统故障可能导致损失
• 政策风险：政策变化可能影响投资

请确保您了解并能承受这些风险。`,
    icon: '⚠️',
  },
};

const Disclaimer: React.FC<DisclaimerProps> = ({
  type = 'general',
  compact = false,
  onAccept,
  className = '',
}) => {
  const [accepted, setAccepted] = useState(false);
  const [expanded, setExpanded] = useState(!compact);

  const disclaimer = DISCLAIMERS[type];

  const handleAccept = () => {
    setAccepted(true);
    onAccept?.();
  };

  if (compact) {
    return (
      <div className={`bg-yellow-50 border border-yellow-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-start">
          <span className="text-lg mr-2">{disclaimer.icon}</span>
          <div className="flex-1">
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-sm font-medium text-yellow-800 hover:text-yellow-900"
            >
              {disclaimer.title}
            </button>
            {expanded && (
              <p className="mt-2 text-xs text-yellow-700 whitespace-pre-line">
                {disclaimer.content}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center">
          <span className="text-2xl mr-3">{disclaimer.icon}</span>
          <h3 className="text-lg font-semibold text-gray-900">{disclaimer.title}</h3>
        </div>
      </div>

      <div className="p-4">
        <div className="prose prose-sm max-w-none">
          <p className="text-gray-700 whitespace-pre-line">{disclaimer.content}</p>
        </div>
      </div>

      {onAccept && (
        <div className="p-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                type="checkbox"
                id={`disclaimer-${type}`}
                checked={accepted}
                onChange={(e) => setAccepted(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label
                htmlFor={`disclaimer-${type}`}
                className="ml-2 text-sm text-gray-700"
              >
                我已阅读并理解上述声明
              </label>
            </div>
            <button
              onClick={handleAccept}
              disabled={!accepted}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              确认
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Inline disclaimer for recommendations
export const InlineDisclaimer: React.FC<{ type?: string }> = ({ type = 'recommendation' }) => {
  const disclaimer = DISCLAIMERS[type as keyof typeof DISCLAIMERS] || DISCLAIMERS.general;

  return (
    <div className="text-xs text-gray-500 italic">
      <span className="font-medium">{disclaimer.icon} {disclaimer.title}:</span>
      {' '}
      本信息仅供参考，不构成投资建议。投资有风险，决策需谨慎。
    </div>
  );
};

// Footer disclaimer
export const FooterDisclaimer: React.FC = () => {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 py-4 px-6">
      <div className="max-w-7xl mx-auto">
        <p className="text-xs text-gray-500 text-center">
          免责声明：本软件提供的所有信息仅供参考，不构成任何投资建议。
          投资有风险，入市需谨慎。在做出任何投资决策之前，请咨询专业的投资顾问。
          本软件不对任何投资损失承担责任。
        </p>
        <p className="text-xs text-gray-400 text-center mt-2">
          © {new Date().getFullYear()} 量化交易建议系统. 保留所有权利.
        </p>
      </div>
    </footer>
  );
};

export default Disclaimer;
