import React, { useState, useEffect, useCallback } from 'react';

interface AsyncTask {
  id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  result?: any;
  error?: string;
  createdAt: string;
  updatedAt: string;
  estimatedCompletion?: string;
}

interface AsyncTaskManagerProps {
  className?: string;
}

const AsyncTaskManager: React.FC<AsyncTaskManagerProps> = ({
  className = '',
}) => {
  const [tasks, setTasks] = useState<AsyncTask[]>([]);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');

  // Fetch tasks
  const fetchTasks = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/tasks');
      const data = await response.json();
      setTasks(data.tasks || []);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  }, []);

  // Poll for updates
  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [fetchTasks]);

  // Cancel task
  const handleCancelTask = async (taskId: string) => {
    try {
      await fetch(`/api/v1/tasks/${taskId}/cancel`, { method: 'POST' });
      fetchTasks();
    } catch (error) {
      console.error('Error cancelling task:', error);
    }
  };

  // Retry task
  const handleRetryTask = async (taskId: string) => {
    try {
      await fetch(`/api/v1/tasks/${taskId}/retry`, { method: 'POST' });
      fetchTasks();
    } catch (error) {
      console.error('Error retrying task:', error);
    }
  };

  // Filter tasks
  const filteredTasks = tasks.filter((task) => {
    if (filter === 'active') {
      return ['pending', 'running'].includes(task.status);
    }
    if (filter === 'completed') {
      return ['completed', 'failed', 'cancelled'].includes(task.status);
    }
    return true;
  });

  // Status badge
  const StatusBadge: React.FC<{ status: AsyncTask['status'] }> = ({ status }) => {
    const config = {
      pending: { label: '等待中', color: 'yellow' },
      running: { label: '运行中', color: 'blue' },
      completed: { label: '已完成', color: 'green' },
      failed: { label: '失败', color: 'red' },
      cancelled: { label: '已取消', color: 'gray' },
    };

    const { label, color } = config[status];

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800`}
      >
        {status === 'running' && (
          <svg
            className="animate-spin -ml-1 mr-1.5 h-3 w-3"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        )}
        {label}
      </span>
    );
  };

  // Progress bar
  const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
        style={{ width: `${progress}%` }}
      ></div>
    </div>
  );

  // Task type icon
  const TaskTypeIcon: React.FC<{ type: string }> = ({ type }) => {
    const icons: Record<string, string> = {
      model_training: '🤖',
      backtesting: '🔬',
      plan_generation: '📋',
      data_fetch: '📊',
      analysis: '📈',
    };

    return <span className="text-lg">{icons[type] || '⚙️'}</span>;
  };

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">后台任务</h2>
          <div className="flex space-x-2">
            {(['all', 'active', 'completed'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-md text-sm font-medium ${
                  filter === f
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {f === 'all' ? '全部' : f === 'active' ? '进行中' : '已完成'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Task List */}
      <div className="divide-y divide-gray-200">
        {filteredTasks.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>暂无任务</p>
          </div>
        ) : (
          filteredTasks.map((task) => (
            <div key={task.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <TaskTypeIcon type={task.type} />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-sm font-medium text-gray-900">
                        {task.type.replace(/_/g, ' ').replace(/\b\w/g, (l) =>
                          l.toUpperCase()
                        )}
                      </h3>
                      <StatusBadge status={task.status} />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      ID: {task.id}
                    </p>

                    {/* Progress */}
                    {task.status === 'running' && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                          <span>进度</span>
                          <span>{task.progress}%</span>
                        </div>
                        <ProgressBar progress={task.progress} />
                        {task.estimatedCompletion && (
                          <p className="text-xs text-gray-400 mt-1">
                            预计完成: {new Date(task.estimatedCompletion).toLocaleTimeString()}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Error */}
                    {task.status === 'failed' && task.error && (
                      <p className="text-xs text-red-600 mt-1">
                        错误: {task.error}
                      </p>
                    )}

                    {/* Result */}
                    {task.status === 'completed' && task.result && (
                      <p className="text-xs text-green-600 mt-1">
                        任务完成
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  {task.status === 'running' && (
                    <button
                      onClick={() => handleCancelTask(task.id)}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      取消
                    </button>
                  )}
                  {task.status === 'failed' && (
                    <button
                      onClick={() => handleRetryTask(task.id)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      重试
                    </button>
                  )}
                </div>
              </div>

              {/* Timestamps */}
              <div className="mt-2 flex space-x-4 text-xs text-gray-400">
                <span>创建: {new Date(task.createdAt).toLocaleString()}</span>
                <span>更新: {new Date(task.updatedAt).toLocaleString()}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AsyncTaskManager;
