import { isArray } from "@vue/shared";

const BASE_URL = "https://6bxwkv84qjspb1-8000.proxy.runpod.net"

type Action =
	| "putDoc"
	| "getDoc"
	| "mergeDoc"
	| "deleteDoc"
	| "findDocs"
	| "scanDocs"
	| "countDocs"
	| "existsDoc";


type JsonSchema = {
	type: string;
	title: string;
	properties: {
		[key: string]: {
			type: string;
			items?: JsonSchema;
			properties?: JsonSchema["properties"];
		};
	};
	required: string[];
};


type Status = {
	code: number;
	message: string;
	key: string;
	definition: JsonSchema;
};

type Message = {
	role: "assistant" | "user" | "system";
	content: string;
}

type Chat = {
	key?: string;
	instructions?: string;
	messages: Message[];
}


const isObject = (value: any): value is object => {
	return value && typeof value === "object" && !isArray(value);
};


function jsonSchemaGenerator(
	target: any,
	key: string,
	descriptor: PropertyDescriptor,
) {
	const originalMethod = descriptor.value;
	const jsonSchema: JsonSchema = {
		title: key,
		type: "object",
		properties: {},
		required: [],
	};

	const generateSchema = (value: any): JsonSchema => {
		if (isArray(value)) {
			return {
				type: "array",
				//@ts-ignore
				items: generateSchema(value[0]),
			};
		} else if (isObject(value)) {
			const nestedSchema: JsonSchema = {
				title: Object.keys(value)[0],
				type: "object",
				properties: {},
				required: [],
			};
			for (const key in value) {
				// @ts-ignore
				nestedSchema.properties[key] = generateSchema(value[key]);
				// @ts-ignore
				if (value[key] !== null) {
					nestedSchema.required.push(key);
				}
			}
			return nestedSchema;
		} else {
			//@ts-ignore
			return { type: typeof value };
		}
	};

	descriptor.value = function (...args: any[]) {
		const result = originalMethod.apply(this, args);
		const keys = Object.keys(result);

		keys.forEach((key) => {
			jsonSchema.properties[key] = generateSchema(result[key]);
			if (result[key] !== null) {
				jsonSchema.required.push(key);
			}
		});

		return jsonSchema;
	};
}


interface IQuipuBase<T> {
	namespace: string;
	action: Action;
	data?: T;
	key?: string;
	limit?: number;
	offset?: number;
	buildUrl(): string;
	run(): Promise<Status | T | T[] | number | boolean>;
}

type QDocument<T> = {
	namespace: string;
	action: Action;
	data?: T;
	key?: string;
	limit?: number;
	offset?: number;
};

export class QuipuBase<T> implements IQuipuBase<T> {
	constructor(
		public namespace: string,
		public action: Action,
		public data?: T,
		public key?: string,
		public limit?: number,
		public offset?: number,
	) { }

	@jsonSchemaGenerator
	getJsonSchema<T>(data: T): JsonSchema {
		return data as unknown as JsonSchema;
	}


	async run(): Promise<Status | T | T[] | number | boolean> {
		const url = this.buildUrl();
		const definition = this.getJsonSchema(this.data);
		const writeOptions = {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({ data: this.data, definition }),
		};
		const readOptions = {
			headers: {
				"Content-Type": "application/json",
			},
			method: "POST",
			body: JSON.stringify({ definition }),
		};
		let response = new Response();
		switch (this.action) {
			case "putDoc":
			case "mergeDoc":
				response = await fetch(url, writeOptions);
				return (await response.json()) as Status;
			case "findDocs":
			case "scanDocs":
				response = await fetch(url, writeOptions);
				return (await response.json()) as T[];
			case "getDoc":
				response = await fetch(url, readOptions);
				return (await response.json()) as T;
			case "deleteDoc":
				response = await fetch(url, readOptions);
				return (await response.json()) as Status;
			case "countDocs":
				response = await fetch(url, readOptions);
				return (await response.text()) as number;
			case "existsDoc":
				response = await fetch(url, readOptions);
				return (await response.text()) as boolean;
				break;
			default:
				throw new Error("Invalid action");
		}
	}
	buildUrl(): string {
		const params = new URLSearchParams();
		params.set("action", this.action);
		if (this.key) params.set("key", this.key);
		if (this.limit) params.set("limit", this.limit.toString());
		if (this.offset) params.set("offset", this.offset.toString());
		const baseUrl = BASE_URL;
		return `${baseUrl}/api/document/${this.namespace}?${params.toString()}`;
	}
}

export type { QDocument, Chat, Message, Status, JsonSchema, Action }