// src/components/Footer.js

import React from 'react';
import { Box, Typography } from '@mui/material';

const Footer = () => {
  return (
    <Box sx={{ p: 2, backgroundColor: '#f5f5f5', textAlign: 'center' }}>
      <Typography variant="body2" color="textSecondary">
        © 2024 Shadow Interview Assistant. All rights reserved.
      </Typography>
    </Box>
  );
};

export default Footer;

