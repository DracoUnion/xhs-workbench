import { request } from './http'
import type { Keyword, Note, Template, Skill, ContentPackage } from '../types/domain'
import type { ApiPage } from '../types/api'

const unwrap = <T>(res: { data: T }): T => res.data
// 内容获客接口后端部分未实现：捕获 404/501 后前端展示“待接入”空态。

export const listKeywords = (productId: number): Promise<Keyword[]> =>
  request<{ data: Keyword[] }>({ url: '/keywords', params: { product_id: productId } }).then(unwrap)

export const createKeyword = (body: Partial<Keyword>): Promise<Keyword> =>
  request<{ data: Keyword }>({ url: '/keywords', method: 'POST', data: body }).then(unwrap)

export const startKeywordCollection = (keywordId: number) =>
  request<{ data: unknown }>({ url: `/keywords/${keywordId}/collect`, method: 'POST' }).then(unwrap)

export const listNotes = (productId?: number, page = 1, pageSize = 20): Promise<ApiPage<Note>> =>
  request<ApiPage<Note>>({ url: '/notes', params: { product_id: productId, page, page_size: pageSize } })

export const getNote = (id: number): Promise<Note> =>
  request<{ data: Note }>({ url: `/notes/${id}` }).then(unwrap)

export const getNoteAnalysis = (id: number): Promise<Record<string, unknown>> =>
  request<{ data: Record<string, unknown> }>({ url: `/notes/${id}/analysis` }).then(unwrap)

export const listTemplates = (productId?: number): Promise<Template[]> =>
  request<{ data: Template[] }>({ url: '/templates', params: { product_id: productId } }).then(unwrap)

export const templateToSkill = (templateId: number) =>
  request<{ data: unknown }>({ url: `/templates/${templateId}/to-skill`, method: 'POST' }).then(unwrap)

export const listSkills = (productId?: number): Promise<Skill[]> =>
  request<{ data: Skill[] }>({ url: '/skills', params: { product_id: productId } }).then(unwrap)

export const getSkill = (id: number): Promise<Skill> =>
  request<{ data: Skill }>({ url: `/skills/${id}` }).then(unwrap)

export const createSkill = (body: Partial<Skill>): Promise<Skill> =>
  request<{ data: Skill }>({ url: '/skills', method: 'POST', data: body }).then(unwrap)

export const updateSkill = (id: number, body: Partial<Skill>): Promise<Skill> =>
  request<{ data: Skill }>({ url: `/skills/${id}`, method: 'PATCH', data: body }).then(unwrap)

export const testSkill = (id: number) =>
  request<{ data: unknown }>({ url: `/skills/${id}/test`, method: 'POST' }).then(unwrap)

export const generateContent = (skillId: number, count = 1) =>
  request<{ data: unknown }>({ url: '/contents/generate', method: 'POST', data: { skill_id: skillId, count } }).then(unwrap)

export const listContentPackages = (skillId?: number, status?: string): Promise<ContentPackage[]> =>
  request<{ data: ContentPackage[] }>({ url: '/contents', params: { skill_id: skillId, status } }).then(unwrap)