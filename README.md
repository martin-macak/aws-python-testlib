# aws-testlib

Contains various utilities and methods for testing SAM and other AWS services that use boto3 and
botocore.

## AWS Api Gateway

### Velocity templates for integration

This library contains methods that allow to inflate Velocity templates in the same way that is supported
by AWS api gateway.

This functionality uses embedded Java jar file that contains all necessary functions. Because of this, Java
runtime is required to be installed on the system.