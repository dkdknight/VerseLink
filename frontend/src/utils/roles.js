export const getRoleLabel = (role, isOwner = false) => {
  if (isOwner) return 'Propriétaire';
  switch (role) {
    case 'admin':
      return 'Admin';
    case 'moderator':
      return 'Modérateur';
    default:
      return 'Membre';
  }
};

export const getRoleBadgeClasses = (role, isOwner = false) => {
  if (isOwner) return 'bg-purple-100 text-purple-800';
  if (role === 'admin') return 'bg-red-100 text-red-800';
  if (role === 'moderator') return 'bg-yellow-100 text-yellow-800';
  return 'bg-gray-100 text-gray-800';
};