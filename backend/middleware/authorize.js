const authorizeRoles = (allowedRoles) => {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({
                success: false,
                message: 'Authentication required'
            });
        }

        if (!allowedRoles.includes(req.user.role)) {
            return res.status(403).json({
                success: false,
                message: 'Access denied. Insufficient privileges.'
            });
        }

        next();
    };
};

// Enhanced authorization for specific features
const authorizeFeature = (feature) => {
    const featurePermissions = {
        'dashboard_analytics': ['admin'],
        'user_management': ['admin'],
        'system_metrics': ['admin'],
        'database_tools': ['admin'],
        'backup_restore': ['admin'],
        'query_console': ['admin', 'staff'],
        'quick_actions': ['admin', 'staff']
    };

    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({
                success: false,
                message: 'Authentication required'
            });
        }

        const allowedRoles = featurePermissions[feature] || [];
        if (!allowedRoles.includes(req.user.role)) {
            return res.status(403).json({
                success: false,
                message: `Access denied. ${feature} is not available for your role.`,
                required_roles: allowedRoles
            });
        }

        next();
    };
};

module.exports = { authorizeRoles, authorizeFeature };
