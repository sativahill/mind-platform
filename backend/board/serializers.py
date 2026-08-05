from rest_framework import serializers

from goals.models import Goal

from .models import (
    BoardTask,
    BoardTaskDependency,
)


class BoardTaskReferenceSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = BoardTask

        fields = (
            "id",
            "title",
            "status",
        )


class BoardTaskSerializer(
    serializers.ModelSerializer
):
    dependency_ids = serializers.PrimaryKeyRelatedField(
        source="dependencies",
        queryset=BoardTask.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    dependencies = BoardTaskReferenceSerializer(
        many=True,
        read_only=True,
    )

    dependent_task_ids = serializers.SerializerMethodField()

    blocking_tasks = serializers.SerializerMethodField()

    is_blocked = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = BoardTask

        fields = (
            "id",
            "goal",
            "title",
            "description",
            "status",
            "priority",
            "importance",
            "source",
            "due_date",
            "completed_at",
            "position_x",
            "position_y",
            "sort_order",
            "dependency_ids",
            "dependencies",
            "dependent_task_ids",
            "is_blocked",
            "blocking_tasks",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "source",
            "completed_at",
            "dependencies",
            "dependent_task_ids",
            "is_blocked",
            "blocking_tasks",
            "created_at",
            "updated_at",
        )

    def get_dependent_task_ids(
        self,
        task,
    ):
        return list(
            task.dependent_tasks.values_list(
                "id",
                flat=True,
            )
        )

    def get_blocking_tasks(
        self,
        task,
    ):
        unfinished_dependencies = (
            task.dependencies.exclude(
                status=BoardTask.DONE,
            )
        )

        return BoardTaskReferenceSerializer(
            unfinished_dependencies,
            many=True,
        ).data

    def validate_title(
        self,
        value,
    ):
        title = value.strip()

        if not title:
            raise serializers.ValidationError(
                "Task title cannot be empty."
            )

        return title

    def validate_description(
        self,
        value,
    ):
        return value.strip()

    def validate_goal(
        self,
        goal: Goal,
    ):
        request = self.context.get(
            "request"
        )

        if (
            request is not None
            and goal.user_id
            != request.user.id
        ):
            raise serializers.ValidationError(
                "You cannot use another user's goal."
            )

        if goal.status == Goal.COMPLETED:
            raise serializers.ValidationError(
                (
                    "Restore the completed goal before "
                    "adding or moving tasks to it."
                )
            )

        if goal.status == Goal.ARCHIVED:
            raise serializers.ValidationError(
                (
                    "Restore the archived goal before "
                    "adding or moving tasks to it."
                )
            )

        return goal

    def validate_dependency_ids(
        self,
        dependencies,
    ):
        request = self.context.get(
            "request"
        )

        dependency_ids = [
            dependency.id
            for dependency in dependencies
        ]

        if (
            len(dependency_ids)
            != len(set(dependency_ids))
        ):
            raise serializers.ValidationError(
                "A dependency cannot be added more than once."
            )

        if request is not None:
            invalid_dependency = next(
                (
                    dependency
                    for dependency in dependencies
                    if dependency.goal.user_id
                    != request.user.id
                ),
                None,
            )

            if invalid_dependency is not None:
                raise serializers.ValidationError(
                    (
                        "You cannot use another user's task "
                        "as a dependency."
                    )
                )

        if self.instance is not None:
            if self.instance.id in dependency_ids:
                raise serializers.ValidationError(
                    "A task cannot depend on itself."
                )

            for dependency in dependencies:
                if self._task_reaches_target(
                    start_task=dependency,
                    target_task=self.instance,
                ):
                    raise serializers.ValidationError(
                        (
                            f'Adding "{dependency.title}" would '
                            "create a circular dependency."
                        )
                    )

        return dependencies

    def validate(
        self,
        attrs,
    ):
        status = attrs.get(
            "status",
            getattr(
                self.instance,
                "status",
                BoardTask.TODO,
            ),
        )

        dependencies = attrs.get(
            "dependencies"
        )

        if dependencies is None:
            if self.instance is not None:
                dependencies = list(
                    self.instance.dependencies.all()
                )
            else:
                dependencies = []

        unfinished_dependencies = [
            dependency
            for dependency in dependencies
            if dependency.status
            != BoardTask.DONE
        ]

        if (
            status
            in (
                BoardTask.IN_PROGRESS,
                BoardTask.DONE,
            )
            and unfinished_dependencies
        ):
            titles = ", ".join(
                dependency.title
                for dependency
                in unfinished_dependencies[:3]
            )

            if (
                len(unfinished_dependencies)
                > 3
            ):
                titles += ", …"

            raise serializers.ValidationError(
                {
                    "status": (
                        "Complete the blocking tasks first: "
                        f"{titles}."
                    )
                }
            )

        return attrs

    def create(
        self,
        validated_data,
    ):
        dependencies = validated_data.pop(
            "dependencies",
            [],
        )

        task = BoardTask.objects.create(
            **validated_data
        )

        self._replace_dependencies(
            task=task,
            dependencies=dependencies,
        )

        return task

    def update(
        self,
        instance,
        validated_data,
    ):
        dependencies = validated_data.pop(
            "dependencies",
            None,
        )

        for field, value in validated_data.items():
            setattr(
                instance,
                field,
                value,
            )

        instance.save()

        if dependencies is not None:
            self._replace_dependencies(
                task=instance,
                dependencies=dependencies,
            )

        return instance

    @staticmethod
    def _replace_dependencies(
        task,
        dependencies,
    ):
        BoardTaskDependency.objects.filter(
            task=task,
        ).delete()

        BoardTaskDependency.objects.bulk_create(
            [
                BoardTaskDependency(
                    task=task,
                    depends_on=dependency,
                )
                for dependency in dependencies
            ]
        )

    @staticmethod
    def _task_reaches_target(
        start_task,
        target_task,
    ):
        visited_ids = set()
        pending_ids = [
            start_task.id
        ]

        while pending_ids:
            current_id = pending_ids.pop()

            if current_id in visited_ids:
                continue

            if current_id == target_task.id:
                return True

            visited_ids.add(
                current_id
            )

            next_ids = (
                BoardTaskDependency.objects.filter(
                    task_id=current_id,
                ).values_list(
                    "depends_on_id",
                    flat=True,
                )
            )

            pending_ids.extend(
                dependency_id
                for dependency_id in next_ids
                if dependency_id
                not in visited_ids
            )

        return False