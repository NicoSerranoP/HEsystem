from distutils.core import setup
setup(
  name = 'hesystem',         # How you named your package folder (MyLib)
  packages = ['hesystem'],   # Chose the same as "name"
  version = '0.3.7.0',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'A data marketplace system for computation over sensitive data',   # Give a short description about your library
  author = 'Nicolas Serrano',                   # Type in your name
  author_email = 'nnicosp@hotmail.com',      # Type in your E-Mail
  url = 'https://github.com/NicoSerranoP/HEsystem',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/NicoSerranoP/HEsystem/archive/0.3.tar.gz',    # I explain this later on
  keywords = ['Homomorphic Encryption', 'Decentralized', 'Data Science'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'requests==2.22.0',
          'tenseal==0.2.0a1',
          'rusty-rlp',
          'numpy',
          'web3',
          'apscheduler',
          'psycopg2',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3.7', #Specify which pyhton versions that you want to support
  ],
)
