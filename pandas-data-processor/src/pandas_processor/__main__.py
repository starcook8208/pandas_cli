"""Allow `python -m pandas_processor` as well as the installed CLI."""
from .entry import main

raise SystemExit(main())
