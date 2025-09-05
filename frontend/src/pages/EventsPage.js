import React from 'react';
import { CalendarDaysIcon } from '@heroicons/react/24/outline';

const EventsPage = () => {
  return (
    <div className="min-h-screen bg-dark-950 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <CalendarDaysIcon className="w-24 h-24 text-gray-600 mx-auto mb-6" />
          <h1 className="text-4xl font-bold text-white mb-4 text-shadow">
            Événements
          </h1>
          <p className="text-xl text-gray-400 mb-8">
            Fonctionnalité disponible dans la Phase 3
          </p>
          <div className="glass-effect rounded-xl p-8 max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-4">Prochainement</h2>
            <p className="text-gray-300 leading-relaxed">
              La gestion complète des événements sera disponible bientôt, incluant :
            </p>
            <ul className="text-left text-gray-300 mt-4 space-y-2">
              <li>• Création et édition d'événements</li>
              <li>• Système d'inscriptions avec rôles</li>
              <li>• Manifeste des vaisseaux</li>
              <li>• Check-in automatique</li>
              <li>• Export calendrier .ics</li>
              <li>• Intégration Discord</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventsPage;