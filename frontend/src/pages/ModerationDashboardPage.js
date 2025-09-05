import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  ClockIcon,
  UserIcon,
  ChartBarIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { moderationService } from '../services/moderationService';
import { autoModerationService } from '../services/autoModerationService';
import { useAuth } from '../App';

const ModerationDashboardPage = () => {
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState({});
  const [autoModerationConfig, setAutoModerationConfig] = useState({});
  const [autoModerationStats, setAutoModerationStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedReport, setSelectedReport] = useState(null);
  const [actionModalOpen, setActionModalOpen] = useState(false);
  const [autoModerationModalOpen, setAutoModerationModalOpen] = useState(false);
  const { user } = useAuth();

  const statusOptions = [
    { value: 'all', label: 'Tous les signalements' },
    { value: 'pending', label: 'En attente' },
    { value: 'investigating', label: 'En cours d\'investigation' },
    { value: 'resolved', label: 'Résolus' },
    { value: 'dismissed', label: 'Rejetés' }
  ];

  const reportTypeLabels = {
    spam: 'Spam',
    harassment: 'Harcèlement',
    inappropriate_content: 'Contenu inapproprié',
    cheating: 'Triche',
    no_show: 'Absence non justifiée',
    griefing: 'Griefing',
    other: 'Autre'
  };

  const statusColors = {
    pending: 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30',
    investigating: 'text-blue-400 bg-blue-900/20 border-blue-500/30',
    resolved: 'text-green-400 bg-green-900/20 border-green-500/30',
    dismissed: 'text-gray-400 bg-gray-900/20 border-gray-500/30'
  };

  useEffect(() => {
    // Check if user is admin
    if (!user || user.role !== 'admin') {
      toast.error('Accès non autorisé - Admin requis');
      return;
    }
    
    loadReports();
    loadStats();
    loadAutoModerationConfig();
    loadAutoModerationStats();
  }, [user, selectedStatus]);

  const loadReports = async () => {
    try {
      setLoading(true);
      const params = {
        limit: 50,
        skip: 0
      };
      
      if (selectedStatus !== 'all') {
        params.status = selectedStatus;
      }
      
      const data = await moderationService.getReports(params);
      setReports(data);
    } catch (error) {
      console.error('Failed to load reports:', error);
      toast.error('Erreur lors du chargement des signalements');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await moderationService.getModerationStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleReport = async (reportId, action, reason, additionalData = {}) => {
    try {
      await moderationService.handleReport(reportId, {
        action,
        reason,
        ...additionalData
      });
      
      toast.success(`Action "${action}" appliquée avec succès`);
      setActionModalOpen(false);
      setSelectedReport(null);
      loadReports();
      loadStats();
    } catch (error) {
      console.error('Failed to handle report:', error);
      toast.error('Erreur lors du traitement du signalement');
    }
  };

  if (!user || user.role !== 'admin') {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Accès restreint</h2>
          <p className="text-gray-400">Cette page est réservée aux administrateurs.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Tableau de bord modération</h1>
          <p className="text-gray-400 mt-2">
            Gérez les signalements et appliquez des actions de modération
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-8 h-8 text-yellow-400" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-white">
                  {stats.reports_by_status?.pending || 0}
                </p>
                <p className="text-gray-400">En attente</p>
              </div>
            </div>
          </div>
          
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <div className="flex items-center">
              <ClockIcon className="w-8 h-8 text-blue-400" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-white">
                  {stats.recent_reports_7d || 0}
                </p>
                <p className="text-gray-400">Cette semaine</p>
              </div>
            </div>
          </div>
          
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <div className="flex items-center">
              <UserIcon className="w-8 h-8 text-red-400" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-white">
                  {stats.banned_users || 0}
                </p>
                <p className="text-gray-400">Utilisateurs bannis</p>
              </div>
            </div>
          </div>
          
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <div className="flex items-center">
              <ChartBarIcon className="w-8 h-8 text-green-400" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-white">
                  {stats.total_reports || 0}
                </p>
                <p className="text-gray-400">Total signalements</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Actions rapides</h3>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={async () => {
                try {
                  const result = await moderationService.unbanExpiredUsers();
                  toast.success(result.message);
                  loadStats();
                } catch (error) {
                  toast.error('Erreur lors du débannissement automatique');
                }
              }}
              className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200"
            >
              <CheckCircleIcon className="w-5 h-5 mr-2" />
              Débannir les utilisateurs expirés
            </button>
            
            <Link
              to="/admin/audit-logs"
              className="inline-flex items-center px-4 py-2 border border-primary-600 text-primary-400 rounded-lg hover:bg-primary-600 hover:text-white transition-colors duration-200"
            >
              <DocumentTextIcon className="w-5 h-5 mr-2" />
              Voir les logs d'audit
            </Link>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700 mb-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Signalements</h3>
            
            <div className="flex items-center space-x-4">
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="form-select rounded-lg bg-dark-700 border-dark-600 text-white focus:border-primary-500 focus:ring-primary-500"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Reports List */}
        <div className="bg-dark-800 rounded-lg border border-dark-700">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="loading-spinner w-8 h-8"></div>
            </div>
          ) : reports.length > 0 ? (
            <div className="divide-y divide-dark-700">
              {reports.map((report) => (
                <div key={report.id} className="p-6 hover:bg-dark-750 transition-colors duration-200">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-start space-x-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${statusColors[report.status]}`}>
                              {report.status === 'pending' ? 'En attente' :
                               report.status === 'investigating' ? 'Investigation' :
                               report.status === 'resolved' ? 'Résolu' :
                               report.status === 'dismissed' ? 'Rejeté' : report.status}
                            </span>
                            
                            <span className="text-sm text-gray-400">
                              {reportTypeLabels[report.type] || report.type}
                            </span>
                            
                            <span className="text-sm text-gray-500">
                              {new Date(report.created_at).toLocaleDateString('fr-FR')}
                            </span>
                          </div>
                          
                          <div className="mb-3">
                            <p className="text-white font-medium mb-1">
                              Signalement contre <span className="text-primary-400">{report.reported_user_handle}</span>
                            </p>
                            <p className="text-gray-300 text-sm">
                              Par <span className="text-gray-400">{report.reporter_user_handle}</span>
                            </p>
                          </div>
                          
                          <p className="text-gray-300 text-sm mb-3">
                            {report.reason}
                          </p>
                          
                          {report.context_url && (
                            <a
                              href={report.context_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary-400 hover:text-primary-300 text-sm"
                            >
                              Voir le contexte →
                            </a>
                          )}
                          
                          {report.action_taken && (
                            <div className="mt-3 p-3 bg-dark-700 rounded-lg">
                              <p className="text-green-400 text-sm font-medium mb-1">Action prise :</p>
                              <p className="text-gray-300 text-sm">{report.action_taken}</p>
                              {report.handled_by_handle && (
                                <p className="text-gray-400 text-xs mt-1">
                                  Par {report.handled_by_handle}
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => {
                          setSelectedReport(report);
                          // Here you would open a detailed view modal
                        }}
                        className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-dark-700 transition-colors duration-200"
                        title="Voir les détails"
                      >
                        <EyeIcon className="w-5 h-5" />
                      </button>
                      
                      {report.status === 'pending' && (
                        <button
                          onClick={() => {
                            setSelectedReport(report);
                            setActionModalOpen(true);
                          }}
                          className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200 text-sm"
                        >
                          Traiter
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <ExclamationTriangleIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-400 mb-2">
                Aucun signalement
              </h3>
              <p className="text-gray-500">
                {selectedStatus === 'all' ? 
                  'Aucun signalement trouvé.' :
                  `Aucun signalement avec le statut "${statusOptions.find(s => s.value === selectedStatus)?.label}".`
                }
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Simple Action Modal (placeholder) */}
      {actionModalOpen && selectedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg max-w-md w-full p-6 border border-dark-600">
            <h3 className="text-lg font-semibold text-white mb-4">
              Traiter le signalement
            </h3>
            <p className="text-gray-300 mb-4">
              Signalement contre <span className="text-primary-400">{selectedReport.reported_user_handle}</span>
            </p>
            
            <div className="flex space-x-3">
              <button
                onClick={() => handleReport(selectedReport.id, 'warning', 'Avertissement pour comportement inapproprié')}
                className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors duration-200"
              >
                Avertissement
              </button>
              <button
                onClick={() => handleReport(selectedReport.id, 'dismiss', 'Signalement non fondé')}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200"
              >
                Rejeter
              </button>
            </div>
            
            <button
              onClick={() => {
                setActionModalOpen(false);
                setSelectedReport(null);
              }}
              className="w-full mt-3 px-4 py-2 text-gray-300 hover:text-white transition-colors duration-200"
            >
              Annuler
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModerationDashboardPage;