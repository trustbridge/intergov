# Import specific use cases (and all that litter from their modules, because
# everything is imported instead of just UC class)
# to dramatically simplify imports of the use cases

from intergov.use_cases.authenticated_object_access import AuthenticatedObjectAccessUseCase  # NOQA

from intergov.use_cases.enqueue_message import EnqueueMessageUseCase  # NOQA
from intergov.use_cases.get_message_by_sender_ref import GetMessageBySenderRefUseCase  # NOQA
from intergov.use_cases.patch_message_metadata import PatchMessageMetadataUseCase  # NOQA
from intergov.use_cases.process_message import ProcessMessageUseCase  # NOQA

from intergov.use_cases.store_object import StoreObjectUseCase  # NOQA

from intergov.use_cases.reject_pending_message import RejectPendingMessageUseCase  # NOQA

from .retrieve_and_store_foreign_documents import RetrieveAndStoreForeignDocumentsUseCase  # NOQA
# to be returned:
# from intergov.use_cases.retrieve_and_store_foreign_documents import *  # NOQA
# from intergov.use_cases.get_message_list import *  # NOQA
