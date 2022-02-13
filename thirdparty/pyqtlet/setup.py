from distutils.core import setup

setup(
    name='pyqtlet',
    packages=[
        'pyqtlet',
        'pyqtlet.web',
        'pyqtlet.web.modules.leaflet_134',
        'pyqtlet.web.modules.leaflet_134.images',
        'pyqtlet.web.modules.leaflet_draw_104',
        'pyqtlet.web.modules.leaflet_draw_104.dist',
        'pyqtlet.web.modules.leaflet_draw_104.dist.images',
        'pyqtlet.leaflet',
        'pyqtlet.leaflet.control',
        'pyqtlet.leaflet.core',
        'pyqtlet.leaflet.layer',
        'pyqtlet.leaflet.layer.marker',
        'pyqtlet.leaflet.layer.tile',
        'pyqtlet.leaflet.layer.vector',
        'pyqtlet.leaflet.map',
    ],
    package_data={
        'pyqtlet.web': ['*'], 'pyqtlet.web.modules': ['*'],
        'pyqtlet.web.modules.leaflet_134': ['*'],
        'pyqtlet.web.modules.leaflet_134.images': ['*'],
        'pyqtlet.web.modules.leaflet_draw_104': ['*'],
        'pyqtlet.web.modules.leaflet_draw_104.dist': ['*'],
        'pyqtlet.web.modules.leaflet_draw_104.dist.images': ['*'],
    },
    version='0.3.3',
    description='Bringing leaflet maps to PyQt',
    author='Samarth Hattangady',
    author_email='samhattangady@gmail.com',
    url='https://github.com/skylarkdrones/pyqtlet',
    keywords=['leaflet', 'pyqt', 'maps'],
    classifiers=[],
)
