import React, { useState, useEffect } from 'react';

export interface ModelConfig {
  id: string;
  name: string;
  type: string;
  description: string;
  hyperparameters: Record<string, any>;
  defaultHyperparameters: Record<string, any>;
}

interface ModelSelectorProps {
  onModelSelect: (config: ModelConfig) => void;
  selectedModel?: ModelConfig | null;
  className?: string;
}

const MODEL_TYPES: ModelConfig[] = [
  {
    id: 'linear_regression',
    name: '线性回归',
    type: 'linear_regression',
    description: '简单有效的基础模型，适合线性关系数据',
    hyperparameters: {},
    defaultHyperparameters: {
      fit_intercept: true,
      normalize: false,
    },
  },
  {
    id: 'random_forest',
    name: '随机森林',
    type: 'random_forest',
    description: '集成学习模型，鲁棒性强，适合非线性关系',
    hyperparameters: {},
    defaultHyperparameters: {
      n_estimators: 100,
      max_depth: 10,
      min_samples_split: 5,
      min_samples_leaf: 2,
      random_state: 42,
    },
  },
  {
    id: 'xgboost',
    name: 'XGBoost',
    type: 'xgboost',
    description: '梯度提升树，性能优异，适合结构化数据',
    hyperparameters: {},
    defaultHyperparameters: {
      n_estimators: 100,
      max_depth: 6,
      learning_rate: 0.1,
      subsample: 0.8,
      colsample_bytree: 0.8,
      random_state: 42,
    },
  },
  {
    id: 'lstm',
    name: 'LSTM',
    type: 'lstm',
    description: '长短期记忆网络，适合时间序列预测',
    hyperparameters: {},
    defaultHyperparameters: {
      hidden_size: 64,
      num_layers: 2,
      dropout: 0.2,
      learning_rate: 0.001,
      epochs: 50,
      batch_size: 32,
    },
  },
  {
    id: 'transformer',
    name: 'Transformer',
    type: 'transformer',
    description: '注意力机制模型，适合复杂序列模式',
    hyperparameters: {},
    defaultHyperparameters: {
      d_model: 128,
      nhead: 8,
      num_encoder_layers: 3,
      dim_feedforward: 512,
      dropout: 0.1,
      learning_rate: 0.0001,
      epochs: 100,
      batch_size: 64,
    },
  },
];

const ModelSelector: React.FC<ModelSelectorProps> = ({
  onModelSelect,
  selectedModel,
  className = '',
}) => {
  const [selectedType, setSelectedType] = useState<string>(
    selectedModel?.type || ''
  );
  const [customHyperparameters, setCustomHyperparameters] = useState<
    Record<string, any>
  >(selectedModel?.hyperparameters || {});
  const [modelName, setModelName] = useState(selectedModel?.name || '');
  const [modelDescription, setModelDescription] = useState(
    selectedModel?.description || ''
  );

  const selectedModelConfig = MODEL_TYPES.find((m) => m.type === selectedType);

  useEffect(() => {
    if (selectedModelConfig) {
      setCustomHyperparameters(selectedModelConfig.defaultHyperparameters);
    }
  }, [selectedType]);

  const handleHyperparameterChange = (key: string, value: any) => {
    setCustomHyperparameters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSubmit = () => {
    if (!selectedModelConfig) return;

    const config: ModelConfig = {
      id: selectedModelConfig.id,
      name: modelName || selectedModelConfig.name,
      type: selectedType,
      description: modelDescription || selectedModelConfig.description,
      hyperparameters: customHyperparameters,
      defaultHyperparameters: selectedModelConfig.defaultHyperparameters,
    };

    onModelSelect(config);
  };

  const renderHyperparameterInput = (key: string, value: any) => {
    const type = typeof value;

    if (type === 'boolean') {
      return (
        <div key={key} className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">{key}</label>
          <input
            type="checkbox"
            checked={customHyperparameters[key] ?? value}
            onChange={(e) =>
              handleHyperparameterChange(key, e.target.checked)
            }
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
        </div>
      );
    }

    if (type === 'number') {
      return (
        <div key={key}>
          <label className="block text-sm font-medium text-gray-700">
            {key}
          </label>
          <input
            type="number"
            value={customHyperparameters[key] ?? value}
            onChange={(e) =>
              handleHyperparameterChange(key, parseFloat(e.target.value))
            }
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
      );
    }

    return (
      <div key={key}>
        <label className="block text-sm font-medium text-gray-700">
          {key}
        </label>
        <input
          type="text"
          value={customHyperparameters[key] ?? value}
          onChange={(e) => handleHyperparameterChange(key, e.target.value)}
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Model Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          选择模型类型
        </label>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {MODEL_TYPES.map((model) => (
            <div
              key={model.id}
              onClick={() => setSelectedType(model.type)}
              className={`relative rounded-lg border p-4 cursor-pointer hover:shadow-md transition-shadow ${
                selectedType === model.type
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 bg-white'
              }`}
            >
              <div className="flex items-center">
                <input
                  type="radio"
                  name="model_type"
                  checked={selectedType === model.type}
                  onChange={() => setSelectedType(model.type)}
                  className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                />
                <label className="ml-3 block text-sm font-medium text-gray-900">
                  {model.name}
                </label>
              </div>
              <p className="mt-1 text-sm text-gray-500">{model.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Model Configuration */}
      {selectedModelConfig && (
        <div className="space-y-4">
          {/* Model Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              模型名称
            </label>
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder={selectedModelConfig.name}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>

          {/* Model Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              模型描述
            </label>
            <textarea
              value={modelDescription}
              onChange={(e) => setModelDescription(e.target.value)}
              placeholder={selectedModelConfig.description}
              rows={3}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>

          {/* Hyperparameters */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              超参数配置
            </h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-4">
              {Object.entries(selectedModelConfig.defaultHyperparameters).map(
                ([key, value]) => renderHyperparameterInput(key, value)
              )}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSubmit}
              className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              确认选择
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
