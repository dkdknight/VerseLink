import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  RocketLaunchIcon,
  UsersIcon,
  CalendarDaysIcon,
  TrophyIcon,
  ArrowRightIcon,
  StarIcon
} from '@heroicons/react/24/outline';
import { organizationService } from '../services/organizationService';

const HomePage = () => {
  const [stats, setStats] = useState({
    organizations: 0,
    events: 0,
    tournaments: 0,
    players: 0
  });
  const [featuredOrgs, setFeaturedOrgs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);
      
      // Load featured organizations
      const orgs = await organizationService.listOrganizations('', 'public', 6);
      setFeaturedOrgs(orgs);
      
      // Mock stats for now (will be replaced with real data)
      setStats({
        organizations: orgs.length,
        events: 42,
        tournaments: 12,
        players: 1337
      });
      
    } catch (error) {
      console.error('Failed to load home data:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, label, value, color = "text-primary-400" }) => (
    <div className="glass-effect rounded-xl p-6 text-center hover:scale-105 transition-transform duration-300">
      <Icon className={`w-12 h-12 ${color} mx-auto mb-4`} />
      <div className="text-3xl font-bold text-white mb-2 stat-counter">
        {value.toLocaleString()}
      </div>
      <div className="text-gray-400 font-medium">{label}</div>
    </div>
  );

  const FeatureCard = ({ icon: Icon, title, description, link, linkText }) => (
    <div className="card-hover p-6">
      <Icon className="w-12 h-12 text-primary-400 mb-4" />
      <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
      <p className="text-gray-400 mb-4 leading-relaxed">{description}</p>
      <Link 
        to={link}
        className="inline-flex items-center text-primary-400 hover:text-primary-300 font-medium transition-colors duration-200"
      >
        {linkText}
        <ArrowRightIcon className="w-4 h-4 ml-2" />
      </Link>
    </div>
  );

  const OrgCard = ({ org }) => (
    <Link 
      to={`/organizations/${org.id}`}
      className="org-card rounded-xl p-6 block hover:scale-105 transition-all duration-300"
    >
      <div className="flex items-center mb-4">
        <div className="w-12 h-12 bg-gradient-star rounded-lg flex items-center justify-center mr-4">
          <span className="text-white font-bold text-lg">{org.tag}</span>
        </div>
        <div>
          <h3 className="text-white font-bold text-lg">{org.name}</h3>
          <div className="flex items-center text-gray-400 text-sm">
            <StarIcon className="w-4 h-4 mr-1" />
            <span>{org.member_count} membres</span>
          </div>
        </div>
      </div>
      
      <p className="text-gray-400 text-sm line-clamp-3 mb-4">
        {org.description || 'Aucune description disponible.'}
      </p>
      
      <div className="flex items-center justify-between text-sm">
        <span className="text-primary-400 font-medium">
          {org.event_count} événements
        </span>
        <span className="text-accent-gold font-medium">
          {org.tournament_count} tournois
        </span>
      </div>
    </Link>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="loading-spinner w-12 h-12"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950">
      {/* Hero Section */}
      <section className="hero-gradient py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex justify-center mb-8">
            <RocketLaunchIcon className="w-24 h-24 text-primary-400 animate-pulse-slow" />
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-8 text-shadow animate-glow">
            VerseLink
          </h1>
          
          <p className="text-xl sm:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
            La plateforme communautaire <span className="text-primary-400 font-semibold">Star Citizen</span> pour 
            connecter les corporations, organiser des événements épiques et participer à des tournois compétitifs.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/organizations" 
              className="btn-primary text-lg px-8 py-4 inline-flex items-center justify-center glow-primary"
            >
              Découvrir les Organisations
              <ArrowRightIcon className="w-5 h-5 ml-2" />
            </Link>
            <Link 
              to="/events" 
              className="btn-secondary text-lg px-8 py-4 inline-flex items-center justify-center"
            >
              Voir les Événements
              <CalendarDaysIcon className="w-5 h-5 ml-2" />
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 -mt-16 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-8">
            <StatCard 
              icon={UsersIcon} 
              label="Organisations" 
              value={stats.organizations} 
              color="text-primary-400"
            />
            <StatCard 
              icon={CalendarDaysIcon} 
              label="Événements" 
              value={stats.events} 
              color="text-accent-green"
            />
            <StatCard 
              icon={TrophyIcon} 
              label="Tournois" 
              value={stats.tournaments} 
              color="text-accent-gold"
            />
            <StatCard 
              icon={RocketLaunchIcon} 
              label="Joueurs" 
              value={stats.players} 
              color="text-accent-orange"
            />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4 text-shadow">
              Fonctionnalités Principales
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Tout ce dont vous avez besoin pour créer une communauté Star Citizen dynamique et organisée.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={UsersIcon}
              title="Organisations"
              description="Créez ou rejoignez des corporations Star Citizen. Gérez les membres, abonnez-vous aux événements d'autres organisations."
              link="/organizations"
              linkText="Explorer les organisations"
            />
            
            <FeatureCard
              icon={CalendarDaysIcon}
              title="Événements"
              description="Organisez des missions, raids, courses et événements communautaires avec système d'inscription et manifeste de vaisseaux."
              link="/events"
              linkText="Voir les événements"
            />
            
            <FeatureCard
              icon={TrophyIcon}
              title="Tournois"
              description="Créez des compétitions avec brackets automatiques, gestion des équipes et système de scores."
              link="/tournaments"
              linkText="Découvrir les tournois"
            />
          </div>
        </div>
      </section>

      {/* Featured Organizations */}
      {featuredOrgs.length > 0 && (
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-dark-900/50">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4 text-shadow">
                Organisations en Vedette
              </h2>
              <p className="text-xl text-gray-400">
                Découvrez les organisations les plus actives de la communauté.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {featuredOrgs.slice(0, 6).map((org) => (
                <OrgCard key={org.id} org={org} />
              ))}
            </div>

            <div className="text-center mt-12">
              <Link 
                to="/organizations" 
                className="btn-primary inline-flex items-center text-lg px-8 py-4"
              >
                Voir toutes les organisations
                <ArrowRightIcon className="w-5 h-5 ml-2" />
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center glass-effect rounded-2xl p-12">
          <h2 className="text-4xl font-bold text-white mb-6 text-shadow">
            Prêt à Rejoindre l'Aventure ?
          </h2>
          <p className="text-xl text-gray-400 mb-8 leading-relaxed">
            Connectez-vous avec Discord et commencez à explorer l'univers Star Citizen 
            avec une communauté passionnée et organisée.
          </p>
          <Link 
            to="/login" 
            className="btn-primary text-xl px-10 py-5 inline-flex items-center glow-primary"
          >
            <svg className="w-6 h-6 mr-3" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419-.0002 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1568 2.4189Z"/>
            </svg>
            Se connecter avec Discord
          </Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;