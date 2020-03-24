class RetrieveAndStoreForeignDocumentsUseCase:

    def __init__(
            self,
            object_retrieval_repo,
            object_lake_repo,
            foreign_object_repo):
        self.object_retrieval = object_retrieval_repo
        self.object_lake = object_lake_repo
        self.foreign_objects = foreign_object_repo

    def execute(self):
        retrieval_task = self.object_retrieval.get()
        if not retrieval_task:
            return False
        else:
            (msg_id, message) = retrieval_task
            fname = self.foreign_objects.get(message)
            if fname:
                posted = self.object_lake.post(fname, message)

            if fname and posted:
                self.object_retrieval.delete(msg_id)
                return True
            else:
                return False
