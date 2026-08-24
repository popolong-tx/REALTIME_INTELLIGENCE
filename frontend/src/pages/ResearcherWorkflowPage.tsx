import React, { useState } from 'react';
import ResearchWorkbench from '../components/ResearchWorkbench';
import AsyncTaskManager from '../components/AsyncTaskManager';
import PlanGenerationWizard from '../components/PlanGenerationWizard';
import { PageHeader, Breadcrumb } from '../components/MainLayout';

const ResearcherWorkflowPage: React.FC = () => {
  const [activeView, setActiveView] = useState<'workbench' | 'wizard' | 'tasks'>('workbench');
  const [showWizard, setShowWizard] = useState(false);

  const handlePlanComplete = (plan: any) => {
    console.log('Plan generated:', plan);
    setShowWizard(false);
    // Show success message or navigate to plan
  };

  return (
    <div>
      <Breadcrumb items={[{ label: '研究员工作流' }]} />

      <PageHeader
        title="研究员工作流"
        description="证券研究、计划生成和任务管理"
        actions={
          <button
            onClick={() => setShowWizard(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            生成交易计划
          </button>
        }
      />

      {/* View Toggle */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setActiveView('workbench')}
          className={`px-4 py-2 rounded-md text-sm font-medium ${
            activeView === 'workbench'
              ? 'bg-blue-100 text-blue-700 border border-blue-300'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          🔍 研究工作台
        </button>
        <button
          onClick={() => setActiveView('tasks')}
          className={`px-4 py-2 rounded-md text-sm font-medium ${
            activeView === 'tasks'
              ? 'bg-blue-100 text-blue-700 border border-blue-300'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          ⚙️ 后台任务
        </button>
      </div>

      {/* Main Content */}
      {showWizard ? (
        <PlanGenerationWizard
          onComplete={handlePlanComplete}
          onCancel={() => setShowWizard(false)}
        />
      ) : (
        <>
          {activeView === 'workbench' && <ResearchWorkbench />}
          {activeView === 'tasks' && <AsyncTaskManager />}
        </>
      )}
    </div>
  );
};

export default ResearcherWorkflowPage;
