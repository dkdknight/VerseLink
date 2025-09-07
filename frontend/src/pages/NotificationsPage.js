import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BellIcon, 
  CheckIcon, 
  Cog6ToothIcon,
  FunnelIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { notificationService } from '../services/notificationService';
import { useAuth } from '../App';

const NotificationsPage = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [selectedType, setSelectedType] = useState('all');
  const [stats, setStats] = useState({});
  const { user } = useAuth();

  const filterOptions = [
    { value: 'all', label: 'Toutes' },
    { value: 'event_created', label: 'Événements créés' },
    { value: 'event_reminder', label: 'Rappels événements' },
    { value: 'tournament_created', label: 'Tournois créés' },
    { value: 'match_result', label: 'Résultats matchs' },
    { value: 'org_member_joined', label: 'Nouveaux membres' },
    { value: 'warning_received', label: 'Avertissements' },
    { value: 'strike_received', label: 'Strikes' },
    { value: 'reputation_changed', label: 'Réputation' },
    { value: 'welcome', label: 'Bienvenue' },
    { value: 'system_update', label: 'Mises à jour système' }
  ];

  useEffect(() => {
    loadNotifications();
    loadStats();
  }, [unreadOnly, selectedType]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const params = {
        limit: 50,
        unread_only: unreadOnly
      };
      
      const data = await notificationService.getNotifications(params);
      
      // Filter by type if selected
      let filteredData = data;
      if (selectedType !== 'all') {
        filteredData = data.filter(notif => notif.type === selectedType);
      }
      
      setNotifications(filteredData);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      toast.error('Erreur lors du chargement des notifications');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await notificationService.getNotificationStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await notificationService.markAsRead(notificationId);
      
      // Update local state
      setNotifications(prev => 
        prev.map(notif => 
          notif.id === notificationId 
            ? { ...notif, is_read: true, read_at: new Date().toISOString() }
            : notif
        )
      );
      
      // Update stats
      setStats(prev => ({
        ...prev,
        unread_count: Math.max(0, prev.unread_count - 1)
      }));
      
      toast.success('Notification marquée comme lue');
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      toast.error('Erreur lors du marquage de la notification');
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      
      // Update local state
      setNotifications(prev => 
        prev.map(notif => ({ ...notif, is_read: true, read_at: new Date().toISOString() }))
      );
      
      // Update stats
      setStats(prev => ({ ...prev, unread_count: 0 }));
      
      toast.success('Toutes les notifications ont été marquées comme lues');
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      toast.error('Erreur lors du marquage des notifications');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent':
        return 'border-l-red-500 bg-red-900/10';
      case 'high':
        return 'border-l-orange-500 bg-orange-900/10';
      case 'normal':
        return 'border-l-blue-500 bg-blue-900/10';
      case 'low':
        return 'border-l-gray-500 bg-gray-900/10';
      default:
        return 'border-l-gray-500 bg-gray-900/10';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'event_created':
      case 'event_updated':
      case 'event_reminder':
        return '📅';
      case 'tournament_created':
      case 'tournament_started':
      case 'match_result':
        return '🏆';
      case 'org_member_joined':
      case 'org_role_changed':
        return '👥';
      case 'warning_received':
      case 'strike_received':
        return '⚠️';
      case 'reputation_changed':
        return '⭐';
      case 'welcome':
        return '👋';
      case 'system_update':
        return '🔄';
      default:
        return '🔔';
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">Notifications</h1>
              <p className="text-gray-400 mt-2">
                Gérez vos notifications et préférences
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link
                to="/notifications/preferences"
                className="inline-flex items-center px-4 py-2 border border-primary-600 rounded-lg text-primary-400 hover:bg-primary-600 hover:text-white transition-colors duration-200"
              >
                <Cog6ToothIcon className="w-5 h-5 mr-2" />
                Préférences
              </Link>
              
              {stats.unread_count > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200"
                >
                  <CheckIcon className="w-5 h-5 mr-2" />
                  Tout marquer comme lu ({stats.unread_count})
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <div className="flex items-center">
              <BellIcon className="w-8 h-8 text-blue-400" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-white">{stats.total_count || 0}</p>
                <p className="text-gray-400">Total</p>
              </div>
            </div>
          </div>
          
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <div className="flex items-center">
              <EyeSlashIcon className="w-8 h-8 text-orange-400" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-white">{stats.unread_count || 0}</p>
                <p className="text-gray-400">Non lues</p>
              </div>
            </div>
          </div>
          
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <div className="flex items-center">
              <EyeIcon className="w-8 h-8 text-green-400" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-white">
                  {(stats.total_count || 0) - (stats.unread_count || 0)}
                </p>
                <p className="text-gray-400">Lues</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-700 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <FunnelIcon className="w-5 h-5 mr-2" />
            Filtres
          </h3>
          
          <div className="flex flex-wrap gap-4">
            {/* Unread only toggle */}
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={unreadOnly}
                onChange={(e) => setUnreadOnly(e.target.checked)}
                className="form-checkbox h-4 w-4 text-primary-600 rounded focus:ring-primary-500 focus:ring-offset-0"
              />
              <span className="ml-2 text-gray-300">Non lues seulement</span>
            </label>
            
            {/* Type filter */}
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="form-select rounded-lg bg-dark-700 border-dark-600 text-white focus:border-primary-500 focus:ring-primary-500"
            >
              {filterOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Notifications List */}
        <div className="bg-dark-800 rounded-lg border border-dark-700">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="loading-spinner w-8 h-8"></div>
            </div>
          ) : notifications.length > 0 ? (
            <div className="divide-y divide-dark-700">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-6 border-l-4 transition-colors duration-200 ${
                    !notification.is_read ? 'bg-dark-750' : 'hover:bg-dark-750'
                  } ${getPriorityColor(notification.priority)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      {/* Type Icon */}
                      <div className="flex-shrink-0 text-2xl">
                        {getTypeIcon(notification.type)}
                      </div>
                      
                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="text-white font-semibold text-lg mb-2">
                              {notification.title}
                            </h4>
                            <p className="text-gray-300 mb-3">
                              {notification.message}
                            </p>
                            
                            {/* Priority Badge */}
                            {notification.priority !== 'normal' && (
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                notification.priority === 'urgent' ? 'bg-red-900/50 text-red-300 border border-red-500/30' :
                                notification.priority === 'high' ? 'bg-orange-900/50 text-orange-300 border border-orange-500/30' :
                                'bg-gray-900/50 text-gray-300 border border-gray-500/30'
                              }`}>
                                {notification.priority === 'urgent' ? 'Urgent' :
                                 notification.priority === 'high' ? 'Important' :
                                 notification.priority === 'low' ? 'Info' : notification.priority}
                              </span>
                            )}
                          </div>
                        </div>
                        
                        {/* Footer */}
                        <div className="flex items-center justify-between mt-4 pt-4 border-t border-dark-600">
                          <span className="text-sm text-gray-400">
                            {notification.time_ago}
                          </span>
                          
                          <div className="flex items-center space-x-3">
                            {notification.action_url && (
                              <Link
                                to={notification.action_url}
                                className="text-sm text-primary-400 hover:text-primary-300 font-medium"
                                onClick={() => {
                                  if (!notification.is_read) {
                                    markAsRead(notification.id);
                                  }
                                }}
                              >
                                Voir →
                              </Link>
                            )}
                            
                            {!notification.is_read && (
                              <button
                                onClick={() => markAsRead(notification.id)}
                                className="inline-flex items-center px-3 py-1 text-sm text-green-400 hover:text-green-300 border border-green-500/30 rounded-lg hover:bg-green-900/20 transition-colors duration-200"
                              >
                                <CheckIcon className="w-4 h-4 mr-1" />
                                Marquer comme lu
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <BellIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-400 mb-2">
                {unreadOnly ? 'Aucune notification non lue' : 'Aucune notification'}
              </h3>
              <p className="text-gray-500">
                {unreadOnly ? 
                  'Toutes vos notifications ont été lues.' :
                  'Vous recevrez ici les notifications des événements, tournois et activités.'
                }
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationsPage;