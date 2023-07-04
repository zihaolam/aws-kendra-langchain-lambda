FROM public.ecr.aws/sam/build-python3.10:1.84.0-20230517004040 as stage1

WORKDIR /app

COPY *.py .

COPY requirements.txt .

RUN ls

RUN pip install -r requirements.txt -t .

RUN rm -rf numpy*

RUN zip -r package.zip *

FROM scratch AS export-stage
COPY --from=stage1 /app/package.zip .