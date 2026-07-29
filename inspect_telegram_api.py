import inspect
from telegram.ext import Application
from telegram.request import Request

print('Application.builder signature:', inspect.signature(Application.builder))
print('Application.builder doc:', Application.builder.__doc__)
print('\nBuilder methods:')
for name in sorted([n for n in dir(Application.builder) if not n.startswith('_')]):
    print(name)

print('\nRequest signature:', inspect.signature(Request))
print('Request doc:', Request.__doc__)
print('\nRequest init args:')
for name, param in inspect.signature(Request).parameters.items():
    print(name, param)
