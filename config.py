"""
Configuration module for navegador project.
Manages paths, environment variables, and application settings.
"""

import os
from pathlib import Path
from typing import Optional
import sys


class Config:
    """Configuration class for managing application settings and paths."""

    def __init__(self):
        """Initialize configuration with environment variables and default values."""
        # Get the project root directory (where this config.py file is located)
        self.project_root = Path(__file__).parent.absolute()

        # Allow override via environment variable
        if 'NAVEGADOR_PROJECT_ROOT' in os.environ:
            self.project_root = Path(os.environ['NAVEGADOR_PROJECT_ROOT']).absolute()

        # Define all paths relative to project root
        self._setup_paths()

        # Verify critical paths exist
        self._verify_paths()

    def _setup_paths(self):
        """Setup all project paths relative to project root."""
        # Data directories
        self.encuestas_path = self._get_path('NAVEGADOR_ENCUESTAS_PATH', 'encuestas')
        self.reportes_path = self._get_path('NAVEGADOR_REPORTES_PATH', 'reportes')
        self.tmp_images_path = self._get_path('NAVEGADOR_TMP_IMAGES_PATH', 'tmp_images')
        self.plot_images_path = self._get_path('NAVEGADOR_PLOT_IMAGES_PATH', 'plot_images')
        self.cuestionarios_path = self._get_path('NAVEGADOR_CUESTIONARIOS_PATH', 'cuestionarios')

        # Database paths
        self.db_path = self._get_path('NAVEGADOR_DB_PATH', 'db_f1')

        # Data files
        self.los_mex_dict_path = self._get_file_path(
            'NAVEGADOR_LOS_MEX_DICT_PATH',
            self.encuestas_path / 'los_mex_dict.pkl'
        )

    def _get_path(self, env_var: str, default_subpath: str) -> Path:
        """
        Get a path from environment variable or use default relative to project root.

        Args:
            env_var: Environment variable name
            default_subpath: Default subdirectory name relative to project root

        Returns:
            Absolute Path object
        """
        if env_var in os.environ:
            return Path(os.environ[env_var]).absolute()
        return (self.project_root / default_subpath).absolute()

    def _get_file_path(self, env_var: str, default_path: Path) -> Path:
        """
        Get a file path from environment variable or use default.

        Args:
            env_var: Environment variable name
            default_path: Default Path object

        Returns:
            Absolute Path object
        """
        if env_var in os.environ:
            return Path(os.environ[env_var]).absolute()
        return default_path

    def _verify_paths(self):
        """Verify that critical paths exist, create directories if needed."""
        # Create directories if they don't exist (except for encuestas which should exist)
        directories_to_create = [
            self.reportes_path,
            self.tmp_images_path,
            self.plot_images_path,
        ]

        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)

        # Verify critical paths exist (don't create these)
        if not self.encuestas_path.exists():
            print(f"WARNING: Encuestas directory not found at {self.encuestas_path}", file=sys.stderr)
            print(f"Set NAVEGADOR_ENCUESTAS_PATH environment variable to specify location", file=sys.stderr)

    def get_path_str(self, path_attr: str) -> str:
        """
        Get a path as a string with trailing slash.

        Args:
            path_attr: Name of the path attribute (e.g., 'encuestas_path')

        Returns:
            String path with trailing slash for backward compatibility
        """
        path = getattr(self, path_attr)
        return str(path) + os.sep

    def __repr__(self):
        """String representation showing all configured paths."""
        return (
            f"Config(\n"
            f"  project_root={self.project_root}\n"
            f"  encuestas_path={self.encuestas_path}\n"
            f"  reportes_path={self.reportes_path}\n"
            f"  tmp_images_path={self.tmp_images_path}\n"
            f"  plot_images_path={self.plot_images_path}\n"
            f"  db_path={self.db_path}\n"
            f"  los_mex_dict_path={self.los_mex_dict_path}\n"
            f")"
        )


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the singleton configuration instance.

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# For backward compatibility, export path strings
config = get_config()
ruta_enc = config.get_path_str('encuestas_path')
ruta_rep = config.get_path_str('reportes_path')
ruta_tmp_images = config.get_path_str('tmp_images_path')
