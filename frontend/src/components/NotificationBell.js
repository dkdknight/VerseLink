import React, { useState, useEffect, useRef } from 'react';
import { 
  BellIcon, 
  CheckIcon, 
  XMarkIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { BellIcon as BellSolidIcon } from '@heroicons/react/24/solid';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { notificationService } from '../services/notificationService';
import { useAuth } from '../App';

const NotificationBell = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      loadNotifications();
      loadStats();
      
      // Refresh notifications every 30 seconds
      const interval = setInterval(() => {
        loadStats();
      }, 30000);
      
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const data = await notificationService.getNotifications({ limit: 10 });
      setNotifications(data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const stats = await notificationService.getNotificationStats();
      setUnreadCount(stats.unread_count);
    } catch (error) {
      console.error('Failed to load notification stats:', error);
    }
  };

  const handleBellClick = async () => {
    if (!isOpen) {
      await loadNotifications();
    }
    setIsOpen(!isOpen);
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
      
      setUnreadCount(prev => Math.max(0, prev - 1));
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
      
      setUnreadCount(0);
      toast.success('Toutes les notifications ont été marquées comme lues');
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      toast.error('Erreur lors du marquage des notifications');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent':
        return 'text-red-400 bg-red-900/20 border-red-500/30';
      case 'high':
        return 'text-orange-400 bg-orange-900/20 border-orange-500/30';
      case 'normal':
        return 'text-blue-400 bg-blue-900/20 border-blue-500/30';
      case 'low':
        return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
      default:
        return 'text-gray-400 bg-gray-900/20 border-gray-500/30';
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
      case 'match_disputed':
        return '⚔️';
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
      default:
        return '🔔';
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={handleBellClick}
        className="relative p-2 text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg"
      >
        {unreadCount > 0 ? (
          <BellSolidIcon className="w-6 h-6 text-primary-400" />
        ) : (
          <BellIcon className="w-6 h-6" />
        )}
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-dark-800 rounded-lg shadow-xl border border-dark-600 z-50 max-h-96 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-dark-600">
            <h3 className="text-lg font-semibold text-white">Notifications</h3>
            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-primary-400 hover:text-primary-300 font-medium"
                >
                  Tout marquer comme lu
                </button>
              )}
              <Link
                to="/notifications/preferences"
                className="p-1 text-gray-400 hover:text-white rounded"
                onClick={() => setIsOpen(false)}
              >
                <Cog6ToothIcon className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-80 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="loading-spinner w-6 h-6"></div>
              </div>
            ) : notifications.length > 0 ? (
              <div className="divide-y divide-dark-600">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-dark-700 transition-colors duration-200 ${
                      !notification.is_read ? 'bg-dark-750' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      {/* Type Icon */}
                      <div className="flex-shrink-0 text-lg">
                        {getTypeIcon(notification.type)}
                      </div>
                      
                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="text-white font-medium text-sm">
                              {notification.title}
                            </h4>
                            <p className="text-gray-400 text-xs mt-1 line-clamp-2">
                              {notification.message}
                            </p>
                            
                            {/* Priority Badge */}
                            {notification.priority !== 'normal' && (
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium mt-2 border ${getPriorityColor(notification.priority)}`}>
                                {notification.priority === 'urgent' ? 'Urgent' :
                                 notification.priority === 'high' ? 'Important' :
                                 notification.priority === 'low' ? 'Info' : notification.priority}
                              </span>
                            )}
                          </div>
                          
                          {/* Actions */}
                          <div className="flex items-center space-x-1 ml-2">
                            {!notification.is_read && (
                              <button
                                onClick={() => markAsRead(notification.id)}
                                className="p-1 text-gray-400 hover:text-green-400 rounded"
                                title="Marquer comme lu"
                              >
                                <CheckIcon className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </div>
                        
                        {/* Time and Action Link */}
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-500">
                            {notification.time_ago}
                          </span>
                          
                          {notification.action_url && (
                            <Link
                              to={notification.action_url}
                              className="text-xs text-primary-400 hover:text-primary-300 font-medium"
                              onClick={() => {
                                if (!notification.is_read) {
                                  markAsRead(notification.id);
                                }
                                setIsOpen(false);
                              }}
                            >
                              Voir →
                            </Link>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <BellIcon className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-400 text-sm">Aucune notification</p>
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="p-3 border-t border-dark-600 text-center">
              <Link
                to="/notifications"
                className="text-sm text-primary-400 hover:text-primary-300 font-medium"
                onClick={() => setIsOpen(false)}
              >
                Voir toutes les notifications
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;